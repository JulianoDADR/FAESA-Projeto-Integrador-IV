"""FonteSimulada e rotas do simulador ao vivo (/talhoes, /simulador/leituras, /historico)."""
from collections import Counter

import pytest

from app import classificador, faixas
from app.fontes import PASSOS_POR_DIA, TALHOES, FonteDeLeituras, FonteSimulada, hora_simulada

PASSO = 600_000_000  # um passo fixo qualquer: os testes nao dependem do relogio


def test_fonte_simulada_cumpre_a_interface():
    assert issubclass(FonteSimulada, FonteDeLeituras)
    fonte = FonteSimulada()
    assert 6 <= len(fonte.talhoes()) <= 8
    assert {t["especie"] for t in fonte.talhoes()} == {"Arabica", "Conilon"}


def test_mesmo_passo_mesma_leitura_e_passos_diferentes_mudam():
    a, b = FonteSimulada(), FonteSimulada()
    assert a.leituras(PASSO) == b.leituras(PASSO)
    assert a.leituras(PASSO) != a.leituras(PASSO + 1)


def test_leituras_ficam_na_faixa_de_treino_e_sao_marcadas_como_simuladas():
    fonte = FonteSimulada()
    for passo in range(PASSO, PASSO + PASSOS_POR_DIA, 7):
        for leitura in fonte.leituras(passo):
            assert leitura["origem"] == "simulado"
            if leitura["umidade_solo"] is None:
                continue
            for nome, info in faixas.variaveis().items():
                minimo, maximo = info["faixa_treino"]
                assert minimo <= leitura[nome] <= maximo, (nome, leitura)


def test_um_dia_simulado_tem_os_tres_estados_e_sem_dados():
    fonte, estados = FonteSimulada(), Counter()
    for passo in range(PASSO, PASSO + PASSOS_POR_DIA * 2, 3):
        for leitura in fonte.leituras(passo):
            estados["sem" if leitura["umidade_solo"] is None else classificador.classificar(leitura)[0]] += 1
    assert {"Verde", "Amarelo", "Vermelho", "sem"} <= set(estados)
    assert estados["Vermelho"] < estados["Verde"] + estados["Amarelo"]  # demonstracao, nao catastrofe


def test_temperatura_sobe_a_tarde():
    fonte = FonteSimulada()
    dia = (PASSO // PASSOS_POR_DIA) * PASSOS_POR_DIA
    madrugada = fonte.leitura("A", dia + 4 * 6)  # 04:00
    tarde = fonte.leitura("A", dia + 15 * 6)     # 15:00
    assert hora_simulada(dia + 15 * 6) == "15:00"
    if madrugada["umidade_solo"] is not None and tarde["umidade_solo"] is not None:
        assert tarde["temperatura"] > madrugada["temperatura"]


def test_rota_simulador_avalia_todos_os_talhoes(cliente):
    d = cliente.get(f"/simulador/leituras?passo={PASSO}").json()
    assert d["passo"] == PASSO and d["origem_dados"] == "simulado" and d["modo_demonstracao"] is True
    assert len(d["leituras"]) == len(TALHOES)
    for item in d["leituras"]:
        assert item["origem_dados"] == "simulado"
        if item["umidade_solo"] is None:
            assert item["classe"] is None and item["proporcoes"] is None  # sem dados: nunca cor de avaliacao
        else:
            assert item["classe"] in ("Verde", "Amarelo", "Vermelho") and item["mensagem"]


def test_rota_simulador_usa_o_mesmo_classificador_do_classificar(cliente):
    item = cliente.get(f"/simulador/leituras?passo={PASSO}&talhao=B").json()["leituras"][0]
    if item["umidade_solo"] is None:
        pytest.skip("talhao sem dados neste passo")
    corpo = {k: item[k] for k in ("especie", "umidade_solo", "temperatura", "umidade_ar")}
    direto = cliente.post("/classificar", json=corpo).json()
    assert direto["classe"] == item["classe"] and direto["proporcoes"] == item["proporcoes"]


def test_talhao_instavel_fica_sem_dados_em_algum_momento(cliente):
    vistos = set()
    for passo in range(PASSO, PASSO + 120, 10):
        item = cliente.get(f"/simulador/leituras?passo={passo}&talhao=H").json()["leituras"][0]
        vistos.add(item["classe"])
    assert None in vistos and vistos - {None}


def test_simular_falha_do_llm_no_simulador(cliente, monkeypatch):
    from app import explicacao
    monkeypatch.setenv("GROQ_API_KEY", "chave-de-teste")
    monkeypatch.setattr(explicacao, "_chamar_llm", lambda _: "As leituras estão dentro do esperado agora.")
    d = cliente.get(f"/simulador/leituras?passo={PASSO}&simular_falha_llm=true").json()
    assert all(i["origem_mensagem"] == "padrao" for i in d["leituras"])


def test_talhao_desconhecido_e_passo_invalido(cliente):
    assert cliente.get("/simulador/leituras?talhao=Z").status_code == 404
    assert cliente.get("/simulador/leituras?passo=-1").status_code == 422
    assert cliente.get("/historico?talhao=Z").status_code == 404


def test_rota_talhoes_e_historico(cliente):
    t = cliente.get("/talhoes").json()
    assert t["origem_dados"] == "simulado" and len(t["talhoes"]) == len(TALHOES)
    h = cliente.get("/historico?talhao=C").json()
    assert len(h) == 24 and all(p["origem"] == "simulado" for p in h)
    assert all((p["classe"] is None) == (p["umidade_solo"] is None) for p in h)
