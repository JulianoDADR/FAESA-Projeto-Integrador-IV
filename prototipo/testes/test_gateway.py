"""Gateway: protocolo, validacao das linhas, buffer local, envio com retentativa e ponta a ponta com a API."""
from datetime import timedelta

import httpx
import pytest
import serial

from app import banco, fontes
from gateway.gateway import ArduinoSimulado, Buffer, Enviador, Gateway, main
from gateway.protocolo import Calibracao, LinhaInvalida, formatar, interpretar
from gateway.validador import Validador

TOKEN = "token-gateway-teste"


# ---------- protocolo ----------
def test_interpreta_linha_completa_e_formatar_e_o_inverso():
    linha = formatar("C", 12, 610, 24.5, 66.0)
    assert linha == "P:C;N:12;S:610;T:24.5;U:66.0"
    assert interpretar(linha) == {"P": "C", "N": 12, "S": 610, "T": 24.5, "U": 66.0}
    assert interpretar("S:500;T:20;U:70") == {"P": None, "N": None, "S": 500, "T": 20.0, "U": 70.0}


@pytest.mark.parametrize("linha", ["", "S:500;T:20", "S:500;T:;U:70", "S:abc;T:20;U:70", "S500;T:20;U:70",
                                   "S:500;S:501;T:20;U:70", "S:2000;T:20;U:70"])
def test_linhas_quebradas_sao_invalidas(linha):
    with pytest.raises(LinhaInvalida):
        interpretar(linha)


def test_calibracao_provisoria_ida_e_volta():
    cal = Calibracao()
    assert cal.para_percentual(cal.bruto_seco) == 0 and cal.para_percentual(cal.bruto_molhado) == 100
    assert abs(cal.para_percentual(cal.para_bruto(55.0)) - 55.0) < 0.2
    assert cal.para_percentual(1000) == 0.0  # mais seco que o "seco" calibrado: limita em 0


# ---------- validacao ----------
def _validador():
    return Validador(talhoes_conhecidos=[t["id"] for t in fontes.TALHOES])


@pytest.mark.parametrize("linha, motivo", [
    ("P:A;N:1;S:610", "mensagem incompleta"),
    ("P:A;N:1;S:610;T:nan;U:nan", "falha no DHT11"),
    ("P:A;N:1;S:1023;T:22;U:70", "sensor de solo desconectado"),
    ("P:A;N:1;S:0;T:22;U:70", "sensor de solo desconectado"),
    ("P:A;N:1;S:610;T:75;U:70", "fora da faixa"),
    ("P:Z;N:1;S:610;T:22;U:70", "ponto desconhecido"),
    ("N:1;S:610;T:22;U:70", "sem ponto"),
])
def test_validador_descarta_com_motivo(linha, motivo):
    r = _validador().validar(linha)
    assert not r.valida and motivo in r.motivo


def test_reenvio_com_mesmo_numero_de_sequencia_e_duplicado():
    v = _validador()
    assert v.validar("P:A;N:7;S:610;T:22;U:70").valida
    r = v.validar("P:A;N:7;S:610;T:22;U:70")
    assert not r.valida and "duplicada" in r.motivo
    assert v.validar("P:B;N:7;S:610;T:22;U:70").valida  # mesmo N em outro ponto e outra leitura


def test_salto_isolado_e_descartado_mas_novo_nivel_confirmado_e_aceito():
    v = _validador()
    for n in range(5):
        assert v.validar(f"P:A;N:{n};S:610;T:22;U:70").valida
    r = v.validar("P:A;N:10;S:610;T:45;U:70")  # +23 graus de uma vez
    assert not r.valida and "oscilação abrupta (temperatura)" in r.motivo
    assert v.validar("P:A;N:11;S:610;T:22.3;U:70").valida  # volta ao normal: o salto era ruido
    # mudanca real e sustentada (chuva forte molhando o solo): aceita na 3a leitura seguida
    resultados = [v.validar(f"P:A;N:{20 + i};S:420;T:22;U:70").valida for i in range(3)]
    assert resultados == [False, False, True]


def test_validador_converte_bruto_para_percentual():
    r = _validador().validar("P:A;N:1;S:625;T:21.04;U:70")
    assert r.valida and r.leitura == {"talhao_id": "A", "umidade_solo": 50.0, "temperatura": 21.0, "umidade_ar": 70.0}


# ---------- buffer e envio ----------
def _leitura(talhao="A", solo=50.0):
    return {"talhao_id": talhao, "umidade_solo": solo, "temperatura": 21.0, "umidade_ar": 70.0}


def _instante(minutos_atras=1):
    return (banco.agora_utc() - timedelta(minutes=minutos_atras)).isoformat(timespec="seconds")


def _cliente_falso(respostas):
    """httpx.Client que devolve as respostas na ordem (status ou excecao) e registra os pedidos."""
    pedidos = []

    def tratar(pedido):
        pedidos.append(pedido)
        resposta = respostas.pop(0)
        if isinstance(resposta, Exception):
            raise resposta
        return httpx.Response(resposta, json={"erros": ["x"]} if resposta >= 400 else {"situacao": "gravada"})
    return httpx.Client(transport=httpx.MockTransport(tratar), base_url="http://api"), pedidos


def test_buffer_guarda_sem_duplicar_e_resume_com_pandas(tmp_path):
    b = Buffer(tmp_path / "buffer.db")
    b.guardar(_leitura(), "2026-11-15T10:00:00+00:00", "simulado")
    b.guardar(_leitura(), "2026-11-15T10:00:00+00:00", "simulado")  # mesma chave: ignora
    b.descartar("falha no DHT11 (nan)", "P:A;S:1;T:nan;U:nan")
    assert len(b.pendentes()) == 1
    assert b.resumo() == {"leituras_validas": 1, "por_situacao": {"pendente": 1}, "descartadas": 1,
                          "descartes_por_motivo": {"falha no DHT11": 1}}


def test_envio_aceito_marca_enviada_e_manda_token(tmp_path):
    b = Buffer(tmp_path / "buffer.db")
    b.guardar(_leitura(), _instante(), "simulado")
    cliente, pedidos = _cliente_falso([201])
    assert Enviador(cliente, TOKEN).enviar_pendentes(b) == 1
    assert pedidos[0].headers["authorization"] == f"Bearer {TOKEN}" and b.pendentes() == []


def test_falha_de_rede_guarda_e_espera_com_backoff_crescente(tmp_path):
    b = Buffer(tmp_path / "buffer.db")
    b.guardar(_leitura(), _instante(), "simulado")
    cliente, pedidos = _cliente_falso([httpx.ConnectError("sem internet"), 500, 201])
    relogio = {"t": 0.0}
    agora = lambda: relogio["t"]  # noqa: E731
    e = Enviador(cliente, TOKEN)
    assert e.enviar_pendentes(b, agora) == 0 and e.falhas_seguidas == 1 and len(b.pendentes()) == 1
    espera_1 = e.proxima_tentativa
    assert e.enviar_pendentes(b, agora) == 0 and len(pedidos) == 1  # ainda esperando: nem tenta
    relogio["t"] = espera_1 + 0.01
    assert e.enviar_pendentes(b, agora) == 0 and e.falhas_seguidas == 2  # 500: tenta de novo depois
    assert e.proxima_tentativa - relogio["t"] >= 1.0 * 0.5  # segunda espera >= 2 s * 0,5 de variacao
    relogio["t"] = e.proxima_tentativa + 0.01
    assert e.enviar_pendentes(b, agora) == 1 and e.falhas_seguidas == 0 and b.pendentes() == []


def test_backoff_tem_teto():
    e = Enviador(None, TOKEN)
    e.falhas_seguidas = 30
    assert e.espera_atual() <= 60.0


def test_recusa_da_api_nao_e_reenviada_e_token_errado_para_o_envio(tmp_path):
    b = Buffer(tmp_path / "buffer.db")
    b.guardar(_leitura("A"), _instante(3), "simulado")
    b.guardar(_leitura("B"), _instante(2), "simulado")
    cliente, pedidos = _cliente_falso([422, 401])
    e = Enviador(cliente, TOKEN)
    e.enviar_pendentes(b)
    assert e.parado_por_configuracao and "401" in e.parado_por_configuracao
    assert [p["talhao_id"] for p in b.pendentes()] == ["B"]  # A foi recusada (nao volta); B continua guardada
    assert e.enviar_pendentes(b) == 0 and len(pedidos) == 2  # parado: nao insiste com token errado


def test_gateway_sem_token_nao_inicia(monkeypatch, tmp_path):
    monkeypatch.delenv("TOKEN_DISPOSITIVO", raising=False)
    monkeypatch.setattr("gateway.gateway._carregar_env", lambda: None)
    assert main(["--simulado", "--ciclos", "1", "--buffer", str(tmp_path / "b.db")]) == 2


# ---------- ponta a ponta: Arduino simulado -> serial virtual -> gateway -> API -> /status ----------
def test_ponta_a_ponta_gateway_simulado_alimenta_a_api_e_parar_deixa_cinza(cliente, monkeypatch, tmp_path):
    monkeypatch.setenv("TOKEN_DISPOSITIVO", TOKEN)
    porta = serial.serial_for_url("loop://", timeout=0.05)
    arduino = ArduinoSimulado(porta, taxa_falhas=0.3)
    buffer = Buffer(tmp_path / "buffer.db")
    gateway = Gateway(porta, _validador(), buffer, Enviador(cliente, TOKEN), origem="simulado")

    for passo in range(600_000_000, 600_000_004):
        arduino.escrever_ciclo(passo)
        gateway.ler_disponiveis(agora=banco.agora_utc() - timedelta(seconds=(600_000_004 - passo) * 5))
    enviadas = gateway.enviador.enviar_pendentes(buffer)
    resumo = buffer.resumo()
    assert enviadas > 0 and enviadas == banco.contar_leituras()
    assert resumo["descartadas"] > 0 and resumo["por_situacao"] == {"enviada": enviadas}

    monkeypatch.setenv("FONTE_LEITURAS", "banco")
    fontes.definir_fonte(None)
    status = cliente.get("/status").json()
    com_cor = [l for l in status["leituras"] if l["classe"]]
    assert status["fonte"] == "banco" and com_cor
    assert all(l["origem_dados"] == "simulado" for l in com_cor)  # modo simulado: tudo marcado como simulado

    # gateway parado: 20 minutos depois, sem novas leituras, tudo fica "sem dados atualizados"
    futuro = banco.agora_utc() + timedelta(minutes=20)
    fontes.definir_fonte(fontes.FonteBanco(minutos_desatualizado=15, relogio=lambda: futuro))
    status = cliente.get("/status").json()
    assert all(l["classe"] is None for l in status["leituras"])
    assert any(l["desatualizada"] for l in status["leituras"])
    porta.close()
