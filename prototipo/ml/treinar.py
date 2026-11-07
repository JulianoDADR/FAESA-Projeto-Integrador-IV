"""Treina e avalia o classificador do AgroAnalise com dados SIMULADOS.

Escolha do algoritmo: arvore de decisao rasa (profundidade 8). E interpretavel
(da para ler as regras), barata e deterministica, adequada a entradas numericas e
a uma saida de 3 classes; combina com a exigencia de interpretabilidade do relatorio (7.4).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier

from gerar_dataset import CLASSES, gerar

PASTA_SAIDA = Path(__file__).parent / "saida"
ATRIBUTOS = ["especie_conilon", "umidade_solo", "temperatura", "umidade_ar"]
AVISO = ("Rótulos gerados por regras sobre as mesmas variáveis de entrada: este resultado valida "
         "o pipeline, não a eficácia agronômica em campo.")


def preparar(quadro):
    x = pd.DataFrame({
        "especie_conilon": (quadro["especie"] == "Conilon").astype(int),
        "umidade_solo": quadro["umidade_solo"],
        "temperatura": quadro["temperatura"],
        "umidade_ar": quadro["umidade_ar"],
    })
    return x[ATRIBUTOS]


def resumir(y_real, y_previsto):
    precisao, revocacao, f1, suporte = precision_recall_fscore_support(
        y_real, y_previsto, labels=CLASSES, zero_division=0)
    por_classe = {c: {"precisao": round(float(precisao[i]), 4), "revocacao": round(float(revocacao[i]), 4),
                      "f1": round(float(f1[i]), 4), "suporte": int(suporte[i])} for i, c in enumerate(CLASSES)}
    return {
        "acuracia": round(float(accuracy_score(y_real, y_previsto)), 4),
        "por_classe": por_classe,
        "media_macro": {"precisao": round(float(precisao.mean()), 4), "revocacao": round(float(revocacao.mean()), 4),
                        "f1": round(float(f1.mean()), 4)},
        "matriz_confusao": confusion_matrix(y_real, y_previsto, labels=CLASSES).tolist(),
    }


def main():
    PASTA_SAIDA.mkdir(exist_ok=True)
    quadro = gerar()
    quadro.to_csv(PASTA_SAIDA / "dataset_simulado.csv", index=False)
    x, y = preparar(quadro), quadro["classe"]
    x_trein, x_teste, y_trein, y_teste = train_test_split(x, y, test_size=0.2, stratify=y, random_state=42)

    linha_base = DummyClassifier(strategy="most_frequent").fit(x_trein, y_trein)
    modelo = DecisionTreeClassifier(max_depth=8, min_samples_leaf=5, random_state=42).fit(x_trein, y_trein)

    metricas = resumir(y_teste, modelo.predict(x_teste))
    base = resumir(y_teste, linha_base.predict(x_teste))
    metricas.update({
        "classes": CLASSES,
        "algoritmo": "DecisionTreeClassifier(max_depth=8, min_samples_leaf=5)",
        "revocacao_vermelho": metricas["por_classe"]["Vermelho"]["revocacao"],
        "falsos_negativos_vermelho": int(sum(metricas["matriz_confusao"][2]) - metricas["matriz_confusao"][2][2]),
        "linha_base": {"estrategia": "classe majoritária (DummyClassifier)", "acuracia": base["acuracia"],
                       "media_macro": base["media_macro"],
                       "revocacao_vermelho": base["por_classe"]["Vermelho"]["revocacao"]},
        "tamanho_treino": int(len(x_trein)), "tamanho_teste": int(len(x_teste)),
        "divisao": "80/20 estratificada (train_test_split, random_state=42)",
        "origem_dados": "simulado",
        "versao_scikit_learn": sklearn.__version__,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "aviso": AVISO,
    })
    joblib.dump({"modelo": modelo, "atributos": ATRIBUTOS, "classes": list(modelo.classes_)},
                PASTA_SAIDA / "modelo.pkl")
    (PASTA_SAIDA / "metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    resumo = {k: metricas[k] for k in ("acuracia", "revocacao_vermelho", "falsos_negativos_vermelho",
                                       "media_macro", "matriz_confusao", "linha_base")}
    print(json.dumps(resumo, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
