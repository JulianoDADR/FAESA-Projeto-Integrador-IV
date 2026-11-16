"""Etapa 5: modo demonstracao, limite de requisicoes, tamanho do corpo, cabecalhos, CORS, teto do LLM e alimentador."""
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app import banco, explicacao, fontes, seguranca

LEITURA = {"especie": "Arabica", "umidade_solo": 55, "temperatura": 21, "umidade_ar": 72}


# ---------- MODO_DEMO ----------
def test_sem_modo_demo_os_recursos_de_demonstracao_ficam_desligados(cliente, monkeypatch):
    monkeypatch.delenv("MODO_DEMO")
    assert cliente.post("/classificar?simular_falha_llm=true", json=LEITURA).status_code == 403
    assert cliente.get("/simulador/leituras").status_code == 403
    assert cliente.get("/status?simular_falha_llm=true").status_code == 403
    # o uso normal continua funcionando
    assert cliente.post("/classificar", json=LEITURA).status_code == 200
    assert cliente.get("/status").status_code == 200
    assert cliente.get("/saude").json()["modo_demo"] is False


def test_com_modo_demo_os_recursos_ficam_ligados(cliente):
    assert cliente.post("/classificar?simular_falha_llm=true", json=LEITURA).json()["origem_mensagem"] == "padrao"
    assert cliente.get("/simulador/leituras").status_code == 200
    assert cliente.get("/saude").json()["modo_demo"] is True


# ---------- limite de requisicoes ----------
def test_limite_por_ip_devolve_429_com_retry_after(cliente):
    respostas = [cliente.post("/classificar", json=LEITURA).status_code for _ in range(31)]
    assert respostas[:30] == [200] * 30 and respostas[30] == 429
    r = cliente.post("/classificar", json=LEITURA)
    assert r.status_code == 429 and int(r.headers["Retry-After"]) >= 1 and "Espere" in r.json()["erros"][0]
    assert cliente.get("/faixas").status_code == 200  # rotas sem limite seguem livres


def test_janela_do_limitador_libera_depois_de_um_minuto():
    relogio = {"t": 0.0}
    limitador = seguranca.LimitadorDeTaxa({("/classificar", "POST"): 2}, relogio=lambda: relogio["t"])
    assert limitador.permitir("1.1.1.1", "/classificar", "POST")[0]
    assert limitador.permitir("1.1.1.1", "/classificar", "POST")[0]
    assert not limitador.permitir("1.1.1.1", "/classificar", "POST")[0]
    assert limitador.permitir("2.2.2.2", "/classificar", "POST")[0]  # outro IP tem a propria conta
    relogio["t"] = 60.1
    assert limitador.permitir("1.1.1.1", "/classificar", "POST")[0]


def test_limitador_reconhece_subrotas_e_metodo():
    limitador = seguranca.LimitadorDeTaxa()
    assert limitador.limite_da_rota("/simulador/leituras", "GET")[1] == 240
    assert limitador.limite_da_rota("/classificar", "GET") == (None, None)
    assert limitador.limite_da_rota("/classificarx", "POST") == (None, None)


# ---------- tamanho do corpo ----------
def test_corpo_grande_demais_e_recusado(cliente):
    grande = '{"especie": "' + "A" * 20000 + '"}'
    r = cliente.post("/classificar", content=grande, headers={"Content-Type": "application/json"})
    assert r.status_code == 413 and "grande demais" in r.json()["erros"][0]


def test_corpo_grande_sem_content_length_tambem_e_recusado(cliente, monkeypatch):
    monkeypatch.setenv("TOKEN_DISPOSITIVO", "t")  # com token certo a rota le o corpo (sem token, recusa antes)
    def pedacos():
        for _ in range(20):
            yield b"x" * 1024
    r = cliente.post("/leituras", content=pedacos(), headers={"Content-Type": "application/json", "Authorization": "Bearer t"})
    assert "content-length" not in {k.lower() for k in r.request.headers}  # envio em pedacos (chunked)
    assert r.status_code == 413 and banco.contar_leituras() == 0


# ---------- cabecalhos e CORS ----------
@pytest.mark.parametrize("caminho", ["/saude", "/index.html"])
def test_cabecalhos_de_seguranca_em_api_e_paginas(cliente, caminho):
    r = cliente.get(caminho)
    assert r.headers["X-Content-Type-Options"] == "nosniff" and r.headers["X-Frame-Options"] == "DENY"
    csp = r.headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in csp and "connect-src 'self'" in csp and "https://cdn.tailwindcss.com" in csp
    assert "camera=()" in r.headers["Permissions-Policy"]
    assert "Strict-Transport-Security" not in r.headers  # so em https


def test_hsts_so_em_https():
    from app.principal import app
    r = TestClient(app, base_url="https://testserver").get("/saude")
    assert r.headers["Strict-Transport-Security"].startswith("max-age=")


def test_sem_origens_permitidas_nao_ha_cors(cliente):
    r = cliente.get("/saude", headers={"Origin": "https://site-estranho.example"})
    assert "access-control-allow-origin" not in r.headers


def test_cors_so_para_as_origens_configuradas(monkeypatch):
    monkeypatch.setenv("ORIGENS_PERMITIDAS", "https://agroanalise.example, https://outra.example")
    from app.principal import criar_app
    c = TestClient(criar_app())
    ok = c.get("/saude", headers={"Origin": "https://agroanalise.example"})
    assert ok.headers["access-control-allow-origin"] == "https://agroanalise.example"
    estranho = c.get("/saude", headers={"Origin": "https://site-estranho.example"})
    assert "access-control-allow-origin" not in estranho.headers


# ---------- teto de chamadas ao LLM ----------
def test_teto_por_minuto_do_llm_cai_na_mensagem_padrao(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "chave-de-teste")
    monkeypatch.setenv("GROQ_MAX_POR_MINUTO", "2")
    chamadas = []
    monkeypatch.setattr(explicacao, "_chamar_llm",
                        lambda _: chamadas.append(1) or "As leituras estão dentro do esperado agora.")
    leituras = [{"especie": "Arabica", "umidade_solo": s, "temperatura": 21.0, "umidade_ar": 72.0} for s in (45, 55, 65)]
    origens = [explicacao.gerar_mensagem("Verde", l)[1] for l in leituras]  # faixas diferentes: sem cache
    assert origens == ["llm", "llm", "padrao"] and len(chamadas) == 2
    uso = explicacao.uso_do_llm()
    assert uso["chamadas"] == 2 and uso["teto_atingido"] == 1 and uso["teto_por_minuto"] == 2


def test_teto_por_dia_e_janela_de_um_minuto(monkeypatch):
    monkeypatch.setenv("GROQ_MAX_POR_MINUTO", "100")
    monkeypatch.setenv("GROQ_MAX_POR_DIA", "3")
    relogio = {"t": 0.0}
    resultados = []
    for i in range(4):
        relogio["t"] = i * 61.0  # um minuto depois do outro: so o teto do dia segura
        resultados.append(explicacao.reservar_chamada(lambda: relogio["t"]))
    assert resultados == [True, True, True, False]


def test_saude_mostra_uso_do_llm_sem_segredo(cliente, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "segredo-que-nao-pode-vazar")
    texto = cliente.get("/saude").text
    assert "segredo-que-nao-pode-vazar" not in texto and "llm_uso" in texto


# ---------- alimentador de demonstracao e semente no startup ----------
def test_alimentador_grava_pelo_caminho_da_ingestao_e_marca_simulado():
    from app import alimentador
    agora = datetime(2026, 11, 15, 18, 0, tzinfo=timezone.utc)
    gravadas = alimentador.gravar_agora(agora)
    assert 6 <= gravadas <= 8 and banco.contar_leituras() == gravadas
    assert alimentador.gravar_agora(agora) == 0  # mesmo instante: idempotente
    with banco.sessao() as s:
        assert {l.origem for l in s.query(banco.Leitura).all()} == {"simulado"}


def test_startup_semeia_banco_vazio_e_liga_alimentador(monkeypatch):
    monkeypatch.setenv("SEMEAR_SE_VAZIO", "1")
    monkeypatch.setenv("ALIMENTADOR_DEMO", "1")
    monkeypatch.setenv("FONTE_LEITURAS", "banco")
    fontes.definir_fonte(None)
    from app.principal import criar_app
    with TestClient(criar_app()) as c:  # o "with" roda o ciclo de vida (startup)
        assert banco.contar_leituras() > 1000  # 72 h de leituras simuladas
        saude = c.get("/saude").json()
        assert saude["alimentador_demo"] is True and saude["fonte_leituras"] == "banco"
        assert any(l["classe"] for l in c.get("/status").json()["leituras"])
