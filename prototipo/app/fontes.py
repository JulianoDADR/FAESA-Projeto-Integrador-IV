"""Fontes de leituras dos talhoes. As paginas consomem a API e nao sabem qual fonte esta ativa.

- FonteDeLeituras: interface.
- FonteSimulada: leituras SIMULADAS, deterministicas (mesmo passo => mesma leitura), sem estado no servidor.
- FonteBanco: leituras gravadas pelo gateway via POST /leituras. Leitura mais antiga que MINUTOS_DESATUALIZADO
  vira "sem dados atualizados" (cinza, nunca cor de avaliacao; relatorio, secao 6.2).

A fonte ativa vem de FONTE_LEITURAS ("simulada", padrao, ou "banco").

O simulador anda em "passos": cada passo = 10 minutos de tempo simulado. O passo atual vem do relogio
(um passo a cada SEGUNDOS_POR_PASSO segundos reais); a interface pode pedir outro passo para pausar ou acelerar.
O modelo e simples e so serve para demonstrar: o solo seca aos poucos e e reposto em ciclos (como uma irrigacao
ou chuva, que o sistema NAO aciona), a temperatura sobe a tarde, a umidade do ar cai com o calor e ha dias com chuva.
"""
import math
import os
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

import numpy as np

SEMENTE = 2026
MINUTOS_POR_PASSO = 10
PASSOS_POR_DIA = 24 * 60 // MINUTOS_POR_PASSO
SEGUNDOS_POR_PASSO = 3

PROPRIEDADE = "Sítio Demonstração (fictício)"
FUSO_EXIBICAO = timezone(timedelta(hours=-3), "BRT")  # horario de Brasilia (sem horario de verao desde 2019)
MINUTOS_DESATUALIZADO_PADRAO = 15

# Parametros ilustrativos de cada ponto de monitoramento (nao representam lavouras reais).
#   solo_topo/solo_fundo: umidade do solo logo apos a reposicao e no fim do ciclo de secagem
#   ciclo: duracao do ciclo de secagem, em passos; fase: deslocamento do ciclo
#   temp_desvio/ar_desvio: microclima do ponto; instavel: sensor que cai de vez em quando
TALHOES = [
    {"id": "A", "nome": "Talhão A", "local": "Encosta sombreada", "especie": "Arabica",
     "solo_topo": 68, "solo_fundo": 44, "ciclo": 180, "fase": 0, "temp_desvio": -1.0, "ar_desvio": 4},
    {"id": "B", "nome": "Talhão B", "local": "Meia encosta", "especie": "Arabica",
     "solo_topo": 64, "solo_fundo": 30, "ciclo": 150, "fase": 40, "temp_desvio": 0.0, "ar_desvio": 0},
    {"id": "C", "nome": "Talhão C", "local": "Topo do morro", "especie": "Arabica",
     "solo_topo": 58, "solo_fundo": 16, "ciclo": 130, "fase": 90, "temp_desvio": 1.5, "ar_desvio": -6},
    {"id": "D", "nome": "Talhão D", "local": "Baixada úmida", "especie": "Arabica",
     "solo_topo": 80, "solo_fundo": 58, "ciclo": 200, "fase": 20, "temp_desvio": -0.5, "ar_desvio": 8},
    {"id": "E", "nome": "Talhão E", "local": "Lavoura nova", "especie": "Conilon",
     "solo_topo": 66, "solo_fundo": 38, "ciclo": 160, "fase": 10, "temp_desvio": 0.0, "ar_desvio": 0},
    {"id": "F", "nome": "Talhão F", "local": "Face norte, mais quente", "especie": "Conilon",
     "solo_topo": 60, "solo_fundo": 20, "ciclo": 120, "fase": 70, "temp_desvio": 3.0, "ar_desvio": -8},
    {"id": "G", "nome": "Talhão G", "local": "Perto do córrego", "especie": "Conilon",
     "solo_topo": 72, "solo_fundo": 45, "ciclo": 170, "fase": 110, "temp_desvio": -1.0, "ar_desvio": 5},
    {"id": "H", "nome": "Talhão H", "local": "Sensor com falhas", "especie": "Conilon",
     "solo_topo": 62, "solo_fundo": 36, "ciclo": 140, "fase": 55, "temp_desvio": 0.5, "ar_desvio": -2,
     "instavel": True},
]
CLIMA = {"Arabica": {"base": 21.0, "amplitude": 4.0}, "Conilon": {"base": 26.0, "amplitude": 4.5}}


def passo_atual(agora=None):
    agora = agora or datetime.now(timezone.utc)
    return int(agora.timestamp() // SEGUNDOS_POR_PASSO)


def hora_simulada(passo):
    minutos = (passo % PASSOS_POR_DIA) * MINUTOS_POR_PASSO
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


class FonteDeLeituras(ABC):
    """Contrato de qualquer fonte de leituras (simulada ou banco)."""
    nome = "abstrata"
    origem = "simulado"

    @abstractmethod
    def talhoes(self):
        """Lista de talhoes (id, nome, local, especie)."""

    @abstractmethod
    def leituras(self, passo=None):
        """Leitura mais recente de cada talhao. Valores ausentes = None (sensor sem dados)."""

    @abstractmethod
    def historico(self, talhao_id, horas=24, passo=None):
        """Uma leitura por hora, da mais antiga para a mais recente."""


class FonteSimulada(FonteDeLeituras):
    nome = "simulada"
    origem = "simulado"

    def __init__(self, semente=SEMENTE):
        self.semente = semente
        self._por_id = {t["id"]: t for t in TALHOES}

    def talhoes(self):
        return _talhoes_cadastrados()

    def _ruido(self, indice, passo):
        return np.random.default_rng([self.semente, indice, passo]).normal(0, 1, 3)

    def _choveu(self, passo):
        """Dia com chuva simulada (cerca de 1 em 3) entre 14h e 17h; devolve o passo de inicio ou None."""
        dia = passo // PASSOS_POR_DIA
        if np.random.default_rng([self.semente, 999, dia]).random() >= 0.35:
            return None
        inicio = dia * PASSOS_POR_DIA + 14 * 60 // MINUTOS_POR_PASSO
        return inicio if passo >= inicio else None

    def _sem_sinal(self, talhao, passo):
        # Sensor instavel: fica sem enviar dados em 1 de cada 5 janelas de 20 passos.
        return talhao.get("instavel", False) and (passo // 20) % 5 == 0

    def leitura(self, talhao_id, passo):
        talhao = self._por_id[talhao_id]
        indice = TALHOES.index(talhao)
        base = {"talhao_id": talhao_id, "especie": talhao["especie"], "passo": passo,
                "hora_simulada": hora_simulada(passo), "hora_leitura": hora_simulada(passo), "origem": self.origem}
        if self._sem_sinal(talhao, passo):
            return base | {"umidade_solo": None, "temperatura": None, "umidade_ar": None}

        ruido = self._ruido(indice, passo)
        # Solo: secagem linear dentro do ciclo, reposta no inicio de cada ciclo.
        k = (passo + talhao["fase"]) % talhao["ciclo"]
        solo = talhao["solo_topo"] - (talhao["solo_topo"] - talhao["solo_fundo"]) * k / talhao["ciclo"]
        # Clima: pico de temperatura por volta das 15h.
        clima = CLIMA[talhao["especie"]]
        hora = (passo % PASSOS_POR_DIA) * MINUTOS_POR_PASSO / 60
        temperatura = clima["base"] + talhao["temp_desvio"] + clima["amplitude"] * math.sin((hora - 9) / 24 * 2 * math.pi)
        ar = 80 + talhao["ar_desvio"] - 2.2 * (temperatura - clima["base"])
        # Chuva simulada: molha o solo (efeito que vai sumindo), esfria e umedece o ar.
        inicio_chuva = self._choveu(passo)
        if inicio_chuva is not None:
            desde = passo - inicio_chuva
            solo += 18 * math.exp(-desde / 36)
            if desde < 18:
                temperatura -= 3.5
                ar = max(ar, 93)
        return base | {
            "umidade_solo": round(float(np.clip(solo + 1.2 * ruido[0], 2, 98)), 1),
            "temperatura": round(float(np.clip(temperatura + 0.4 * ruido[1], 6, 41)), 1),
            "umidade_ar": round(float(np.clip(ar + 1.5 * ruido[2], 20, 99)), 1),
            "chovendo": inicio_chuva is not None and passo - inicio_chuva < 18,
        }

    def leituras(self, passo=None):
        passo = passo_atual() if passo is None else passo
        return [self.leitura(t["id"], passo) for t in TALHOES]

    def historico(self, talhao_id, horas=24, passo=None):
        passo = passo_atual() if passo is None else passo
        por_hora = 60 // MINUTOS_POR_PASSO
        return [self.leitura(talhao_id, passo - por_hora * (horas - 1 - i)) for i in range(horas)]


def _talhoes_cadastrados():
    return [{k: t[k] for k in ("id", "nome", "local", "especie")} | {"propriedade": PROPRIEDADE} for t in TALHOES]


class FonteBanco(FonteDeLeituras):
    """Leituras gravadas pelo gateway. `relogio` pode ser trocado nos testes."""
    nome = "banco"
    origem = "banco"

    def __init__(self, minutos_desatualizado=None, relogio=None):
        self.minutos_desatualizado = minutos_desatualizado or float(
            os.getenv("MINUTOS_DESATUALIZADO", MINUTOS_DESATUALIZADO_PADRAO))
        self.relogio = relogio or (lambda: datetime.now(timezone.utc))

    def talhoes(self):
        return _talhoes_cadastrados()

    @staticmethod
    def _hora(instante):
        return instante.astimezone(FUSO_EXIBICAO).strftime("%H:%M")

    def _vazia(self, talhao_id, especie, ultima=None, desatualizada=False):
        return {"talhao_id": talhao_id, "especie": especie, "passo": None, "hora_simulada": None,
                "hora_leitura": self._hora(ultima.coletado_em) if ultima else None,
                "coletado_em": ultima.coletado_em.isoformat() if ultima else None,
                "origem": ultima.origem if ultima else "sem leitura", "desatualizada": desatualizada,
                "umidade_solo": None, "temperatura": None, "umidade_ar": None}

    def _como_dict(self, linha):
        return {"talhao_id": linha.talhao_id, "especie": linha.especie, "passo": None, "hora_simulada": None,
                "hora_leitura": self._hora(linha.coletado_em), "coletado_em": linha.coletado_em.isoformat(),
                "origem": linha.origem, "desatualizada": False, "umidade_solo": linha.umidade_solo,
                "temperatura": linha.temperatura, "umidade_ar": linha.umidade_ar}

    def leituras(self, passo=None):
        from sqlalchemy import select

        from app import banco
        limite = self.relogio() - timedelta(minutes=self.minutos_desatualizado)
        resultado = []
        with banco.sessao() as s:
            for t in TALHOES:
                ultima = s.scalars(select(banco.Leitura).where(banco.Leitura.talhao_id == t["id"], banco.Leitura.valida)
                                   .order_by(banco.Leitura.coletado_em.desc()).limit(1)).first()
                if ultima is None:
                    resultado.append(self._vazia(t["id"], t["especie"]))
                elif ultima.coletado_em < limite:
                    resultado.append(self._vazia(t["id"], t["especie"], ultima, desatualizada=True))
                else:
                    resultado.append(self._como_dict(ultima))
        return resultado

    def historico(self, talhao_id, horas=24, passo=None):
        """Uma leitura por hora (a ultima de cada hora); hora sem leitura vira ponto sem dados."""
        from sqlalchemy import select

        from app import banco
        fim = self.relogio()
        inicio = fim - timedelta(hours=horas)
        especie = next(t["especie"] for t in TALHOES if t["id"] == talhao_id)
        with banco.sessao() as s:
            linhas = s.scalars(select(banco.Leitura).where(
                banco.Leitura.talhao_id == talhao_id, banco.Leitura.valida, banco.Leitura.coletado_em > inicio,
                banco.Leitura.coletado_em <= fim).order_by(banco.Leitura.coletado_em)).all()
        pontos = []
        for i in range(horas):
            de, ate = inicio + timedelta(hours=i), inicio + timedelta(hours=i + 1)
            dentro = [l for l in linhas if de < l.coletado_em <= ate]
            if dentro:
                pontos.append(self._como_dict(dentro[-1]))
            else:
                vazio = self._vazia(talhao_id, especie)
                vazio["hora_leitura"] = self._hora(ate)
                pontos.append(vazio)
        return pontos


_fonte_ativa = None


def criar_fonte(nome=None):
    nome = (nome or os.getenv("FONTE_LEITURAS") or "simulada").strip().lower()
    if nome == "banco":
        return FonteBanco()
    if nome == "simulada":
        return FonteSimulada()
    raise ValueError(f"FONTE_LEITURAS desconhecida: {nome} (use 'simulada' ou 'banco')")


def definir_fonte(fonte):
    global _fonte_ativa
    _fonte_ativa = fonte


def fonte_ativa():
    global _fonte_ativa
    if _fonte_ativa is None:
        _fonte_ativa = criar_fonte()
    return _fonte_ativa
