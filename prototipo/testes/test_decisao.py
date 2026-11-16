"""Regra de decisao do semaforo e metricas do treino (limiar/peso do Vermelho e teto de referencia)."""
import json
from pathlib import Path

import numpy as np

from app.decisao import decidir

CLASSES = ["Verde", "Amarelo", "Vermelho"]
METRICAS = Path(__file__).resolve().parent.parent / "ml" / "saida" / "metricas.json"


def test_sem_limiar_vale_a_maior_proporcao():
    previstas, regra = decidir([[0.6, 0.3, 0.1], [0.1, 0.2, 0.7]], CLASSES, None)
    assert list(previstas) == ["Verde", "Vermelho"] and not regra.any()


def test_limiar_conservador_puxa_para_vermelho():
    proporcoes = [[0.1, 0.65, 0.25], [0.1, 0.75, 0.15]]
    previstas, regra = decidir(proporcoes, CLASSES, 0.2)
    assert list(previstas) == ["Vermelho", "Amarelo"]
    assert list(regra) == [True, False]  # so a primeira linha mudou por causa da regra


def test_limiar_nunca_tira_um_vermelho():
    gerador = np.random.default_rng(0)
    proporcoes = gerador.dirichlet([1, 1, 1], size=500)
    sem, _ = decidir(proporcoes, CLASSES, None)
    for limiar in (0.5, 0.3, 0.1):
        com, _ = decidir(proporcoes, CLASSES, limiar)
        assert set(np.flatnonzero(sem == "Vermelho")) <= set(np.flatnonzero(com == "Vermelho"))


def test_limiar_meio_desempata_a_favor_do_vermelho():
    previstas, _ = decidir([[0.0, 0.5, 0.5]], CLASSES, 0.5)
    assert previstas[0] == "Vermelho"
    previstas, _ = decidir([[0.0, 0.5, 0.5]], CLASSES, None)
    assert previstas[0] == "Amarelo"


def test_metricas_tem_teto_decisao_e_comparacoes():
    m = json.loads(METRICAS.read_text(encoding="utf-8"))
    decisao = m["decisao"]
    assert decisao["peso_vermelho"] in (1, 2, 3, 4)
    assert decisao["limiar_vermelho"] is None or 0 < decisao["limiar_vermelho"] <= 0.5
    assert decisao["meta_atingida_no_teste"] == (m["revocacao_vermelho"] >= 0.90)
    # a escolha veio da validacao cruzada, que tem uma linha por combinacao
    assert decisao["validacao_cruzada_escolhida"] in decisao["validacao_cruzada_todas"]
    for chave in ("sem_ajuste_conservador", "alternativa_so_limiar", "teto_referencia"):
        assert 0 <= m[chave]["acuracia"] <= 1 and len(m[chave]["matriz_confusao"]) == 3
    assert m["teto_referencia"]["acuracia"] > m["linha_base"]["acuracia"]
    assert "valida o pipeline, não a eficácia agronômica" in m["aviso"]


def test_api_aplica_a_regra_salva_no_modelo(cliente):
    from app import classificador
    params = classificador.parametros_decisao()
    d = cliente.post("/classificar", json={"especie": "Conilon", "umidade_solo": 10, "temperatura": 31,
                                           "umidade_ar": 50}).json()
    assert d["decisao"] == params | {"regra_conservadora_aplicada": d["decisao"]["regra_conservadora_aplicada"]}
