"""Gateway local do AgroAnalise (relatorio, secoes 7.3, 8.2 e 8.4): Arduino -> serial -> validacao -> SQLite local -> API.

Uso (dentro de prototipo/):
  python -m gateway.gateway --simulado --api http://localhost:8000              # sem Arduino: porta virtual loop://
  python -m gateway.gateway --porta COM3 --talhao A --api https://<sua-api>     # com o Arduino ligado

O token vem de TOKEN_DISPOSITIVO (variavel de ambiente ou prototipo/.env). Nunca e impresso.

Fluxo: cada linha recebida pela serial e validada (gateway/validador.py). Leituras validas vao para o buffer SQLite
local (historico + fila de envio) e sao enviadas a API por POST /leituras. Se a rede ou a API falharem, ficam na
fila e o envio e retomado com espera exponencial (backoff com variacao aleatoria). Leituras recusadas pela API
(422/409) nao sao reenviadas. No modo simulado, TODO dado sai com origem = "simulado".
"""
import argparse
import logging
import os
import random
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd
import serial

from gateway.protocolo import Calibracao, formatar
from gateway.validador import Validador

RAIZ = Path(__file__).resolve().parent.parent
BUFFER_PADRAO = RAIZ / "dados" / "gateway_buffer.db"
ESPERA_MAXIMA_S = 60.0
registro = logging.getLogger("agroanalise.gateway")


# ---------------------------------------------------------------- buffer local (SQLite)
class Buffer:
    """Historico local e fila de envio. Sobrevive a quedas do gateway e da internet."""

    def __init__(self, caminho=BUFFER_PADRAO):
        Path(caminho).parent.mkdir(parents=True, exist_ok=True)
        self.conexao = sqlite3.connect(str(caminho))
        self.conexao.executescript("""
            CREATE TABLE IF NOT EXISTS leituras_locais (
                id INTEGER PRIMARY KEY, talhao_id TEXT NOT NULL, coletado_em TEXT NOT NULL,
                umidade_solo REAL, temperatura REAL, umidade_ar REAL, origem TEXT NOT NULL,
                situacao TEXT NOT NULL DEFAULT 'pendente',  -- pendente | enviada | recusada
                tentativas INTEGER NOT NULL DEFAULT 0, ultimo_erro TEXT,
                UNIQUE (talhao_id, coletado_em));
            CREATE TABLE IF NOT EXISTS descartes (
                id INTEGER PRIMARY KEY, recebido_em TEXT NOT NULL, motivo TEXT NOT NULL, linha TEXT);
        """)
        self.conexao.commit()

    def guardar(self, leitura, coletado_em, origem):
        self.conexao.execute(
            "INSERT OR IGNORE INTO leituras_locais (talhao_id, coletado_em, umidade_solo, temperatura, umidade_ar, origem)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (leitura["talhao_id"], coletado_em, leitura["umidade_solo"], leitura["temperatura"], leitura["umidade_ar"], origem))
        self.conexao.commit()

    def descartar(self, motivo, linha):
        self.conexao.execute("INSERT INTO descartes (recebido_em, motivo, linha) VALUES (?, ?, ?)",
                             (datetime.now(timezone.utc).isoformat(), motivo, linha[:200]))
        self.conexao.commit()

    def pendentes(self, limite=50):
        cursor = self.conexao.execute(
            "SELECT id, talhao_id, coletado_em, umidade_solo, temperatura, umidade_ar, origem FROM leituras_locais"
            " WHERE situacao = 'pendente' ORDER BY coletado_em LIMIT ?", (limite,))
        colunas = [c[0] for c in cursor.description]
        return [dict(zip(colunas, linha)) for linha in cursor.fetchall()]

    def marcar(self, ident, situacao, erro=None):
        self.conexao.execute("UPDATE leituras_locais SET situacao = ?, tentativas = tentativas + 1, ultimo_erro = ?"
                             " WHERE id = ?", (situacao, erro, ident))
        self.conexao.commit()

    def falhou(self, ident, erro):
        self.conexao.execute("UPDATE leituras_locais SET tentativas = tentativas + 1, ultimo_erro = ? WHERE id = ?",
                             (erro, ident))
        self.conexao.commit()

    def resumo(self):
        """Resumo com Pandas: situacao das leituras e descartes por motivo."""
        leituras = pd.read_sql_query("SELECT talhao_id, situacao FROM leituras_locais", self.conexao)
        descartes = pd.read_sql_query("SELECT motivo FROM descartes", self.conexao)
        por_situacao = leituras["situacao"].value_counts().to_dict() if len(leituras) else {}
        motivos = (descartes["motivo"].str.replace(r" \(.*\)$", "", regex=True).value_counts().to_dict()
                   if len(descartes) else {})
        return {"leituras_validas": int(len(leituras)), "por_situacao": {k: int(v) for k, v in por_situacao.items()},
                "descartadas": int(len(descartes)), "descartes_por_motivo": {k: int(v) for k, v in motivos.items()}}


# ---------------------------------------------------------------- envio para a API
class Enviador:
    """POST /leituras com token; retentativa com backoff exponencial e variacao aleatoria."""

    def __init__(self, cliente, token):
        self.cliente = cliente
        self.token = token
        self.falhas_seguidas = 0
        self.proxima_tentativa = 0.0
        self.parado_por_configuracao = None

    def espera_atual(self):
        if self.falhas_seguidas == 0:
            return 0.0
        base = min(ESPERA_MAXIMA_S, 2 ** (self.falhas_seguidas - 1))
        return base * random.uniform(0.5, 1.0)

    def enviar_pendentes(self, buffer, agora=time.monotonic):
        """Envia o que estiver na fila. Devolve quantas foram aceitas nesta rodada."""
        if self.parado_por_configuracao or agora() < self.proxima_tentativa:
            return 0
        aceitas = 0
        for item in buffer.pendentes():
            corpo = {k: item[k] for k in ("talhao_id", "coletado_em", "umidade_solo", "temperatura", "umidade_ar", "origem")}
            try:
                resposta = self.cliente.post("/leituras", json=corpo, headers={"Authorization": f"Bearer {self.token}"})
            except httpx.HTTPError as erro:
                return self._falha(buffer, item, f"rede: {type(erro).__name__}", agora, aceitas)
            if resposta.status_code in (200, 201):
                buffer.marcar(item["id"], "enviada")
                aceitas += 1
            elif resposta.status_code in (409, 422):
                buffer.marcar(item["id"], "recusada", _erros(resposta))  # nao adianta reenviar
                registro.warning("API recusou a leitura de %s: %s", item["talhao_id"], _erros(resposta))
            elif resposta.status_code in (401, 403, 503):
                self.parado_por_configuracao = f"HTTP {resposta.status_code}: {_erros(resposta)}"
                registro.error("Envio parado: %s (confira TOKEN_DISPOSITIVO no gateway e no servidor)",
                               self.parado_por_configuracao)
                return aceitas
            else:  # 429, 5xx: tentar de novo mais tarde
                return self._falha(buffer, item, f"HTTP {resposta.status_code}", agora, aceitas)
        self.falhas_seguidas = 0
        return aceitas

    def _falha(self, buffer, item, motivo, agora, aceitas):
        buffer.falhou(item["id"], motivo)
        self.falhas_seguidas += 1
        espera = self.espera_atual()
        self.proxima_tentativa = agora() + espera
        registro.warning("Envio falhou (%s). Nova tentativa em %.1f s; as leituras ficam guardadas.", motivo, espera)
        return aceitas


def _erros(resposta):
    try:
        return "; ".join(resposta.json().get("erros", []))[:200]
    except ValueError:
        return resposta.text[:200]


# ---------------------------------------------------------------- Arduino simulado (porta virtual)
class ArduinoSimulado:
    """Escreve, numa porta virtual loop:// do PySerial, linhas no protocolo do Arduino para cada talhao.

    Os valores vem da FonteSimulada (mesmo simulador das paginas). Para testar o gateway de verdade, injeta falhas
    com semente fixa: linha incompleta, DHT11 com nan, sensor de solo solto, reenvio e salto absurdo.
    """

    def __init__(self, porta, semente=7, taxa_falhas=0.08):
        from app.fontes import FonteSimulada, TALHOES  # importa so no modo simulado
        self.porta = porta
        self.fonte = FonteSimulada()
        self.talhoes = [t["id"] for t in TALHOES]
        self.sorteio = random.Random(semente)
        self.taxa_falhas = taxa_falhas
        self.sequencia = {t: 0 for t in self.talhoes}
        self.calibracao = Calibracao()

    def escrever_ciclo(self, passo):
        for talhao in self.talhoes:
            leitura = self.fonte.leitura(talhao, passo)
            if leitura["umidade_solo"] is None:
                continue  # sensor sem sinal: o Arduino nao manda nada
            self.sequencia[talhao] = (self.sequencia[talhao] + 1) % 65536
            linha = formatar(talhao, self.sequencia[talhao], self.calibracao.para_bruto(leitura["umidade_solo"]),
                             leitura["temperatura"], leitura["umidade_ar"])
            if self.sorteio.random() < self.taxa_falhas:
                linha = self._estragar(linha, talhao, leitura)
            self.porta.write((linha + "\n").encode("ascii"))
            if self.sorteio.random() < 0.02:  # reenvio da mesma linha (mesmo N)
                self.porta.write((linha + "\n").encode("ascii"))

    def _estragar(self, linha, talhao, leitura):
        tipo = self.sorteio.choice(["incompleta", "nan", "solto", "salto"])
        if tipo == "incompleta":
            return linha[: len(linha) // 2]
        if tipo == "nan":
            return formatar(talhao, self.sequencia[talhao], self.calibracao.para_bruto(leitura["umidade_solo"]), None, None)
        if tipo == "solto":
            return formatar(talhao, self.sequencia[talhao], 1023, leitura["temperatura"], leitura["umidade_ar"])
        return formatar(talhao, self.sequencia[talhao], self.calibracao.para_bruto(leitura["umidade_solo"]),
                        leitura["temperatura"] + 25, leitura["umidade_ar"])


# ---------------------------------------------------------------- laco principal
class Gateway:
    def __init__(self, porta, validador, buffer, enviador, origem):
        self.porta, self.validador, self.buffer, self.enviador, self.origem = porta, validador, buffer, enviador, origem

    def ler_disponiveis(self, agora=None):
        """Le todas as linhas que chegaram na serial, valida e guarda. Devolve (validas, descartadas)."""
        validas = descartadas = 0
        while True:
            bruto = self.porta.readline()
            if not bruto:
                break
            linha = bruto.decode("ascii", errors="replace").strip()
            resultado = self.validador.validar(linha)
            if resultado.valida:
                instante = (agora or datetime.now(timezone.utc)).isoformat(timespec="seconds")
                self.buffer.guardar(resultado.leitura, instante, self.origem)
                validas += 1
            else:
                self.buffer.descartar(resultado.motivo, linha)
                registro.info("Descartada (%s): %r", resultado.motivo, linha)
                descartadas += 1
        return validas, descartadas

    def ciclo(self):
        validas, descartadas = self.ler_disponiveis()
        enviadas = self.enviador.enviar_pendentes(self.buffer)
        return validas, descartadas, enviadas


def _carregar_env():
    try:
        from dotenv import load_dotenv
        load_dotenv(RAIZ / ".env")
    except ImportError:
        pass


def main(argv=None):
    argumentos = argparse.ArgumentParser(description="Gateway local do AgroAnálise (serial -> validação -> SQLite -> API).")
    modo = argumentos.add_mutually_exclusive_group(required=True)
    modo.add_argument("--simulado", action="store_true", help="sem Arduino: gera linhas numa porta virtual (origem=simulado)")
    modo.add_argument("--porta", help="porta serial do Arduino (ex.: COM3 ou /dev/ttyUSB0)")
    argumentos.add_argument("--api", default="http://localhost:8000", help="endereço da API")
    argumentos.add_argument("--talhao", help="ponto de monitoramento, se o Arduino não mandar P:")
    argumentos.add_argument("--baud", type=int, default=9600)
    argumentos.add_argument("--intervalo", type=float, default=5.0, help="segundos entre ciclos")
    argumentos.add_argument("--ciclos", type=int, default=0, help="parar depois de N ciclos (0 = sem fim)")
    argumentos.add_argument("--buffer", default=str(BUFFER_PADRAO), help="arquivo SQLite local")
    argumentos.add_argument("--bruto-seco", type=float, default=None, help="calibração: leitura bruta no solo seco")
    argumentos.add_argument("--bruto-molhado", type=float, default=None, help="calibração: leitura bruta no solo encharcado")
    opcoes = argumentos.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # nao imprime cada requisicao (nem cabecalhos)

    _carregar_env()
    token = os.getenv("TOKEN_DISPOSITIVO")
    if not token:
        print("Defina TOKEN_DISPOSITIVO (o mesmo do servidor) antes de iniciar o gateway.", file=sys.stderr)
        return 2
    if opcoes.api.startswith("http://") and not any(h in opcoes.api for h in ("localhost", "127.0.0.1")):
        registro.warning("A API não está em HTTPS. Fora da máquina local, use https:// (o token viaja no cabeçalho).")

    calibracao = Calibracao(opcoes.bruto_seco or Calibracao.bruto_seco, opcoes.bruto_molhado or Calibracao.bruto_molhado)
    from app.fontes import TALHOES
    validador = Validador(calibracao, talhao_padrao=opcoes.talhao, talhoes_conhecidos=[t["id"] for t in TALHOES])
    buffer = Buffer(opcoes.buffer)
    cliente = httpx.Client(base_url=opcoes.api, timeout=10.0)
    enviador = Enviador(cliente, token)

    if opcoes.simulado:
        porta = serial.serial_for_url("loop://", timeout=0.2)
        arduino, origem = ArduinoSimulado(porta), "simulado"
        registro.info("Modo SIMULADO: porta virtual loop://, todas as leituras com origem=simulado.")
    else:
        porta = serial.Serial(opcoes.porta, opcoes.baud, timeout=0.5)
        arduino, origem = None, "dispositivo"
        registro.info("Lendo o Arduino em %s (%d baud).", opcoes.porta, opcoes.baud)
    gateway = Gateway(porta, validador, buffer, enviador, origem)

    ciclo = 0
    try:
        while not opcoes.ciclos or ciclo < opcoes.ciclos:
            if arduino:
                from app.fontes import passo_atual
                arduino.escrever_ciclo(passo_atual())
            validas, descartadas, enviadas = gateway.ciclo()
            ciclo += 1
            registro.info("Ciclo %d: %d válidas, %d descartadas, %d enviadas, %d na fila.",
                          ciclo, validas, descartadas, enviadas, len(buffer.pendentes(1000)))
            if enviador.parado_por_configuracao:
                break
            time.sleep(opcoes.intervalo)
    except KeyboardInterrupt:
        registro.info("Gateway parado pelo usuário.")
    finally:
        enviador.enviar_pendentes(buffer)
        print("Resumo do gateway:", buffer.resumo())
        porta.close()
        cliente.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
