"""config/faixas.json e a fonte unica das faixas: gerador do dataset, validacao e API leem dele."""
import sys
from pathlib import Path

from app import faixas, validacao

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ml"))
import gerar_dataset  # noqa: E402


def test_config_tem_as_tres_variaveis_e_as_duas_especies():
    config = faixas.carregar_faixas()
    assert set(config["variaveis"]) == {"umidade_solo", "temperatura", "umidade_ar"}
    assert {"Arabica", "Conilon"} <= set(config["rotulagem"])
    assert "PROVISÓRIAS" in config["aviso"]


def test_faixa_de_treino_cabe_no_limite_fisico_e_ideal_cabe_no_treino():
    config = faixas.carregar_faixas()
    for nome, info in config["variaveis"].items():
        fis_min, fis_max = info["limite_fisico"]
        tre_min, tre_max = info["faixa_treino"]
        assert fis_min <= tre_min < tre_max <= fis_max, nome
        for especie in ("Arabica", "Conilon"):
            inicio, fim, margem = config["rotulagem"][especie][nome]
            assert tre_min <= inicio < fim <= tre_max and margem > 0, (especie, nome)


def test_gerador_e_validacao_usam_o_mesmo_arquivo():
    config = faixas.carregar_faixas()
    for nome, info in config["variaveis"].items():
        assert gerar_dataset.LIMITES[nome] == tuple(info["faixa_treino"])
        assert validacao.LIMITES[nome][:2] == tuple(float(x) for x in info["limite_fisico"])
    assert gerar_dataset.FAIXAS["Conilon"]["temperatura"] == tuple(config["rotulagem"]["Conilon"]["temperatura"])


def test_dataset_respeita_a_faixa_de_treino():
    quadro = gerar_dataset.gerar(num_amostras=400)
    for nome, (minimo, maximo) in gerar_dataset.LIMITES.items():
        assert quadro[nome].between(minimo, maximo).all(), nome


def test_api_avisa_quando_entrada_sai_do_treino(cliente, leitura_valida):
    dentro = cliente.post("/classificar", json=leitura_valida).json()
    assert dentro["aviso_fora_da_faixa_de_treino"] is False and dentro["variaveis_fora_da_faixa_de_treino"] == []

    fora = cliente.post("/classificar", json=dict(leitura_valida, temperatura=50)).json()
    assert fora["aviso_fora_da_faixa_de_treino"] is True
    assert fora["variaveis_fora_da_faixa_de_treino"] == ["temperatura"]
    assert fora["classe"] in ("Verde", "Amarelo", "Vermelho")  # valor fisicamente possivel: ainda classifica


def test_rota_faixas_serve_o_arquivo(cliente):
    d = cliente.get("/faixas").json()
    assert d["variaveis"]["temperatura"]["faixa_treino"] == [5, 42]
