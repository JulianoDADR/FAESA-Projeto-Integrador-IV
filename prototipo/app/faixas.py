"""Leitura de config/faixas.json: fonte unica das faixas de treino, de rotulagem (provisorias) e dos limites da interface."""
import json
from functools import lru_cache
from pathlib import Path

CAMINHO_FAIXAS = Path(__file__).resolve().parent.parent / "config" / "faixas.json"


@lru_cache(maxsize=1)
def carregar_faixas():
    return json.loads(CAMINHO_FAIXAS.read_text(encoding="utf-8"))


def variaveis():
    return carregar_faixas()["variaveis"]


def fora_da_faixa_de_treino(leitura):
    """Lista as variaveis (ja validadas) que ficaram fora do intervalo visto no treino do modelo."""
    fora = []
    for nome, info in variaveis().items():
        minimo, maximo = info["faixa_treino"]
        if not minimo <= leitura[nome] <= maximo:
            fora.append(nome)
    return fora
