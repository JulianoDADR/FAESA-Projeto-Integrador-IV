"""Carrega o modelo treinado (Scikit-Learn) e classifica uma leitura ja validada."""
from pathlib import Path

import joblib
import pandas as pd

from app.decisao import decidir

CAMINHO_MODELO = Path(__file__).resolve().parent.parent / "ml" / "saida" / "modelo.pkl"
ROTULOS = {"Verde": "Ideal", "Amarelo": "Atenção", "Vermelho": "Ação crítica"}
CLASSES = list(ROTULOS)

_pacote = None


def carregar_modelo(caminho=CAMINHO_MODELO):
    global _pacote
    if _pacote is None:
        if not Path(caminho).exists():
            raise FileNotFoundError("Modelo não encontrado. Rode: python ml/treinar.py --salvar")
        _pacote = joblib.load(caminho)
    return _pacote


def modelo_disponivel():
    return CAMINHO_MODELO.exists()


def parametros_decisao():
    pacote = carregar_modelo()
    return {"peso_vermelho": pacote.get("peso_vermelho", 1), "limiar_vermelho": pacote.get("limiar_vermelho")}


def classificar(leitura):
    """leitura: dicionario ja validado. Devolve (classe, proporcoes por classe, regra_conservadora_aplicada).

    As proporcoes sao a fracao de amostras de treino parecidas (mesma folha da arvore) em cada classe,
    ponderada pelo class_weight do treino (com peso 3, cada Vermelho conta 3 vezes).
    NAO sao confianca nem probabilidade calibrada.
    """
    pacote = carregar_modelo()
    linha = pd.DataFrame([{
        "especie_conilon": 1 if leitura["especie"] == "Conilon" else 0,
        "umidade_solo": leitura["umidade_solo"],
        "temperatura": leitura["temperatura"],
        "umidade_ar": leitura["umidade_ar"],
    }])[pacote["atributos"]]
    modelo = pacote["modelo"]
    ordem = [list(modelo.classes_).index(c) for c in CLASSES]
    proporcoes = modelo.predict_proba(linha)[:, ordem]
    previstas, regra = decidir(proporcoes, CLASSES, pacote.get("limiar_vermelho"))
    por_classe = {c: round(float(p), 4) for c, p in zip(CLASSES, proporcoes[0])}
    return str(previstas[0]), por_classe, bool(regra[0])
