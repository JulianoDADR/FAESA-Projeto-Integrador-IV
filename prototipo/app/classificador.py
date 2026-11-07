"""Carrega o modelo treinado (Scikit-Learn) e classifica uma leitura ja validada."""
from pathlib import Path

import joblib
import pandas as pd

CAMINHO_MODELO = Path(__file__).resolve().parent.parent / "ml" / "saida" / "modelo.pkl"
ROTULOS = {"Verde": "Ideal", "Amarelo": "Atenção", "Vermelho": "Ação crítica"}

_pacote = None


def carregar_modelo(caminho=CAMINHO_MODELO):
    global _pacote
    if _pacote is None:
        if not Path(caminho).exists():
            raise FileNotFoundError("Modelo não encontrado. Rode: python ml/treinar.py")
        _pacote = joblib.load(caminho)
    return _pacote


def modelo_disponivel():
    return CAMINHO_MODELO.exists()


def classificar(leitura):
    """leitura: dicionario ja validado. Devolve (classe, probabilidades por classe)."""
    pacote = carregar_modelo()
    linha = pd.DataFrame([{
        "especie_conilon": 1 if leitura["especie"] == "Conilon" else 0,
        "umidade_solo": leitura["umidade_solo"],
        "temperatura": leitura["temperatura"],
        "umidade_ar": leitura["umidade_ar"],
    }])[pacote["atributos"]]
    modelo = pacote["modelo"]
    probabilidades = modelo.predict_proba(linha)[0]
    por_classe = {c: round(float(p), 4) for c, p in zip(modelo.classes_, probabilidades)}
    classe = max(por_classe, key=por_classe.get)
    return classe, {c: por_classe.get(c, 0.0) for c in ROTULOS}
