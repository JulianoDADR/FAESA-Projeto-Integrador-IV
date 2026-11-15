"""POST /leituras (token, validacao, idempotencia), FonteBanco (dado desatualizado), /status e /disponibilidade."""
from datetime import datetime, timedelta, timezone

import pytest

from app import banco, fontes, indicadores

TOKEN = "token-de-teste-123"


@pytest.fixture
def com_token(monkeypatch):
    monkeypatch.setenv("TOKEN_DISPOSITIVO", TOKEN)
    return {"Authorization": f"Bearer {TOKEN}"}


def leitura(**mudancas):
    base = {"talhao_id": "A", "coletado_em": (datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            "umidade_solo": 52.0, "temperatura": 21.5, "umidade_ar": 74.0, "origem": "simulado"}
    return base | mudancas


# ---------- autenticacao ----------
def test_sem_token_configurado_o_recebimento_fica_desligado(cliente):
    r = cliente.post("/leituras", json=leitura(), headers={"Authorization": "Bearer qualquer"})
    assert r.status_code == 503 and "TOKEN_DISPOSITIVO" in r.json()["erros"][0]


@pytest.mark.parametrize("cabecalho", [None, "Bearer errado", "Basic abc", f"bearer {TOKEN}"])
def test_token_ausente_ou_errado_e_recusado(cliente, com_token, cabecalho):
    r = cliente.post("/leituras", json=leitura(), headers={"Authorization": cabecalho} if cabecalho else {})
    assert r.status_code == 401
    assert banco.contar_leituras() == 0


# ---------- gravacao e idempotencia ----------
def test_leitura_valida_e_gravada_com_especie_do_cadastro(cliente, com_token):
    r = cliente.post("/leituras", json=leitura(talhao_id="E"), headers=com_token)
    assert r.status_code == 201 and r.json()["especie"] == "Conilon"
    assert banco.contar_leituras() == 1


def test_reenvio_igual_e_idempotente_e_valor_diferente_e_conflito(cliente, com_token):
    corpo = leitura()
    assert cliente.post("/leituras", json=corpo, headers=com_token).status_code == 201
    r = cliente.post("/leituras", json=corpo, headers=com_token)
    assert r.status_code == 200 and r.json()["situacao"] == "duplicada"
    assert cliente.post("/leituras", json=corpo | {"umidade_solo": 10.0}, headers=com_token).status_code == 409
    assert banco.contar_leituras() == 1


def test_mesmo_instante_em_outro_fuso_e_a_mesma_leitura(cliente, com_token):
    instante = datetime.now(timezone.utc).replace(microsecond=0) - timedelta(minutes=2)
    brasilia = instante.astimezone(timezone(timedelta(hours=-3)))
    assert cliente.post("/leituras", json=leitura(coletado_em=instante.isoformat()), headers=com_token).status_code == 201
    r = cliente.post("/leituras", json=leitura(coletado_em=brasilia.isoformat()), headers=com_token)
    assert r.status_code == 200 and r.json()["situacao"] == "duplicada"


# ---------- requisicoes malformadas ----------
@pytest.mark.parametrize("corpo, trecho", [
    (leitura(comando="ligar bomba"), "Campo não permitido"),
    ({k: v for k, v in leitura().items() if k != "temperatura"}, "Falta informar"),
    (leitura(talhao_id="Z"), "desconhecido"),
    (leitura(origem="real"), "origem"),
    (leitura(umidade_solo="seco"), "número"),
    (leitura(coletado_em="ontem"), "ISO 8601"),
    (leitura(coletado_em="2026-11-15T10:00:00"), "fuso"),
    (leitura(coletado_em=(datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()), "futuro"),
    (leitura(coletado_em=(datetime.now(timezone.utc) - timedelta(days=40)).isoformat()), "antigo"),
    ([1, 2, 3], "objeto"),
])
def test_requisicoes_malformadas_sao_recusadas(cliente, com_token, corpo, trecho):
    r = cliente.post("/leituras", json=corpo, headers=com_token)
    assert r.status_code == 422 and trecho in " ".join(r.json()["erros"])
    assert banco.contar_leituras() == 0


def test_json_invalido_e_recusado(cliente, com_token):
    r = cliente.post("/leituras", content=b"{nao e json", headers=com_token | {"Content-Type": "application/json"})
    assert r.status_code == 422


def test_valor_fora_do_possivel_e_recusado_e_contado(cliente, com_token):
    r = cliente.post("/leituras", json=leitura(temperatura=85.0), headers=com_token)
    assert r.status_code == 422 and banco.contar_leituras() == 0
    a = next(p for p in indicadores.disponibilidade(72)["por_talhao"] if p["talhao_id"] == "A")
    assert a["rejeitadas"] == 1 and a["validas"] == 0


# ---------- FonteBanco e dado desatualizado ----------
def _gravar(talhao, minutos_atras, solo=55.0, agora=None):
    agora = agora or datetime.now(timezone.utc)
    corpo = leitura(talhao_id=talhao, umidade_solo=solo, coletado_em=(agora - timedelta(minutes=minutos_atras)).isoformat())
    from app import ingestao
    return ingestao.registrar(corpo, agora=agora)


def test_fonte_banco_mostra_a_leitura_mais_recente():
    _gravar("A", 30, solo=40.0)
    _gravar("A", 2, solo=60.0)
    a = next(l for l in fontes.FonteBanco(minutos_desatualizado=15).leituras() if l["talhao_id"] == "A")
    assert a["umidade_solo"] == 60.0 and a["desatualizada"] is False and a["origem"] == "simulado"


def test_leitura_antiga_vira_sem_dados_e_nunca_cor(cliente, monkeypatch):
    _gravar("B", 40)
    monkeypatch.setenv("FONTE_LEITURAS", "banco")
    monkeypatch.setenv("MINUTOS_DESATUALIZADO", "15")
    fontes.definir_fonte(None)
    b = cliente.get("/status?talhao=B").json()["leituras"][0]
    assert b["classe"] is None and b["desatualizada"] is True and b["proporcoes"] is None
    assert b["atualizado_em"] is not None and "antiga" in b["mensagem"]  # mostra quando foi a ultima leitura


def test_gateway_parado_deixa_o_painel_cinza_com_o_passar_do_tempo():
    agora = datetime.now(timezone.utc)
    _gravar("C", 1, agora=agora)
    relogio = {"agora": agora}
    fonte = fontes.FonteBanco(minutos_desatualizado=15, relogio=lambda: relogio["agora"])
    assert next(l for l in fonte.leituras() if l["talhao_id"] == "C")["umidade_solo"] is not None
    relogio["agora"] = agora + timedelta(minutes=20)  # ninguem mais enviou nada
    assert next(l for l in fonte.leituras() if l["talhao_id"] == "C")["umidade_solo"] is None


def test_talhao_que_nunca_enviou_fica_sem_dados(cliente, monkeypatch):
    monkeypatch.setenv("FONTE_LEITURAS", "banco")
    fontes.definir_fonte(None)
    d = cliente.get("/status").json()
    assert d["fonte"] == "banco" and all(l["classe"] is None for l in d["leituras"])
    assert all(l["origem_dados"] == "sem leitura" for l in d["leituras"])


def test_status_com_banco_classifica_pelo_mesmo_caminho(cliente, com_token, monkeypatch):
    cliente.post("/leituras", json=leitura(talhao_id="A", umidade_solo=55.0, temperatura=21.0, umidade_ar=72.0),
                 headers=com_token)
    monkeypatch.setenv("FONTE_LEITURAS", "banco")
    fontes.definir_fonte(None)
    a = cliente.get("/status?talhao=A").json()["leituras"][0]
    direto = cliente.post("/classificar", json={"especie": "Arabica", "umidade_solo": 55, "temperatura": 21,
                                                "umidade_ar": 72}).json()
    assert a["classe"] == direto["classe"] and a["origem_dados"] == "simulado"


def test_historico_do_banco_tem_um_ponto_por_hora_e_buracos_sem_dados():
    agora = datetime.now(timezone.utc)
    for horas_atras in (0.2, 1.5, 5.5):
        _gravar("D", int(horas_atras * 60), agora=agora)
    h = fontes.FonteBanco(relogio=lambda: agora).historico("D", 24)
    assert len(h) == 24
    assert sum(p["umidade_solo"] is not None for p in h) == 3


def test_simulador_continua_simulado_mesmo_com_fonte_banco(cliente, monkeypatch):
    monkeypatch.setenv("FONTE_LEITURAS", "banco")
    fontes.definir_fonte(None)
    d = cliente.get("/simulador/leituras?passo=600000000").json()
    assert d["fonte"] == "simulada" and d["origem_dados"] == "simulado"


def test_fonte_desconhecida_e_erro_claro(monkeypatch):
    with pytest.raises(ValueError):
        fontes.criar_fonte("planilha")


# ---------- disponibilidade ----------
def test_disponibilidade_conta_validas_sobre_esperadas(monkeypatch):
    monkeypatch.setenv("INTERVALO_LEITURA_MIN", "60")  # 1 envio por hora => 3 esperadas em 3 h
    agora = datetime.now(timezone.utc)
    for minutos in (10, 70, 130):
        _gravar("G", minutos, agora=agora)
    d = indicadores.disponibilidade(3, agora=agora)
    g = next(p for p in d["por_talhao"] if p["talhao_id"] == "G")
    assert g["esperadas"] == 3 and g["validas"] == 3 and g["disponibilidade"] == 1.0 and g["meta_atingida"]
    h = next(p for p in d["por_talhao"] if p["talhao_id"] == "H")
    assert h["disponibilidade"] == 0.0 and not h["meta_atingida"]
    assert d["meta"] == 0.95


def test_rota_disponibilidade(cliente):
    d = cliente.get("/disponibilidade?horas=72").json()
    assert d["janela_horas"] == 72 and len(d["por_talhao"]) == 8 and "observacao" in d
