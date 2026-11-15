"""Treina e avalia o classificador do AgroAnalise com dados SIMULADOS.

Uso:
  python ml/treinar.py            # treina e mostra as metricas (nao grava nada)
  python ml/treinar.py --salvar   # tambem grava dataset_simulado.csv, modelo.pkl e metricas.json em ml/saida/

Escolha do algoritmo: arvore de decisao rasa (profundidade 8). E interpretavel (da para ler as regras),
barata e deterministica, adequada a entradas numericas e a uma saida de 3 classes (relatorio, 7.4).

Revocacao do Vermelho (meta do relatorio >= 0,90): comparamos duas alavancas, sozinhas e combinadas:
  - class_weight: peso maior para o Vermelho no treino da arvore;
  - limiar conservador: Vermelho quando a proporcao do Vermelho >= limiar (app/decisao.py).
A combinacao e escolhida por validacao cruzada estratificada (k=5) SO no conjunto de treino: entre as que atingem
revocacao do Vermelho >= 0,90, a de maior F1 macro; se nenhuma atingir, a de maior revocacao. O conjunto de
teste so e usado no fim, uma vez, para relatar os numeros.

Teto de referencia: a propria regra de rotulagem aplicada as leituras SEM ruido, comparada aos rotulos (que foram
gerados com ruido de medicao). Nenhum modelo que ve so as leituras deve passar muito disso.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.tree import DecisionTreeClassifier

from gerar_dataset import CLASSES, gerar, rotular

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.decisao import decidir  # noqa: E402

PASTA_SAIDA = Path(__file__).parent / "saida"
ATRIBUTOS = ["especie_conilon", "umidade_solo", "temperatura", "umidade_ar"]
VARIAVEIS = ["umidade_solo", "temperatura", "umidade_ar"]
PROFUNDIDADE, FOLHA_MINIMA, SEMENTE = 8, 5, 42
META_REVOCACAO_VERMELHO = 0.90
PESOS_VERMELHO = [1, 2, 3, 4]
LIMIARES = [None, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1]  # None = sem regra (vale a maior proporcao)
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


def nova_arvore(peso_vermelho):
    pesos = None if peso_vermelho == 1 else {"Verde": 1, "Amarelo": 1, "Vermelho": peso_vermelho}
    return DecisionTreeClassifier(max_depth=PROFUNDIDADE, min_samples_leaf=FOLHA_MINIMA,
                                  class_weight=pesos, random_state=SEMENTE)


def resumir(y_real, y_previsto):
    precisao, revocacao, f1, suporte = precision_recall_fscore_support(
        y_real, y_previsto, labels=CLASSES, zero_division=0)
    por_classe = {c: {"precisao": round(float(precisao[i]), 4), "revocacao": round(float(revocacao[i]), 4),
                      "f1": round(float(f1[i]), 4), "suporte": int(suporte[i])} for i, c in enumerate(CLASSES)}
    matriz = confusion_matrix(y_real, y_previsto, labels=CLASSES).tolist()
    return {
        "acuracia": round(float(accuracy_score(y_real, y_previsto)), 4),
        "por_classe": por_classe,
        "media_macro": {"precisao": round(float(precisao.mean()), 4), "revocacao": round(float(revocacao.mean()), 4),
                        "f1": round(float(f1.mean()), 4)},
        "matriz_confusao": matriz,
        "revocacao_vermelho": por_classe["Vermelho"]["revocacao"],
        "falsos_negativos_vermelho": int(sum(matriz[2]) - matriz[2][2]),
    }


def regra_sem_ruido(quadro):
    """Aplica a regra de rotulagem as leituras guardadas (sem o ruido usado para gerar os rotulos)."""
    previstas = pd.Series(index=quadro.index, dtype=object)
    for especie in ("Arabica", "Conilon"):
        parte = quadro[quadro["especie"] == especie]
        niveis = rotular(especie, {v: parte[v].to_numpy() for v in VARIAVEIS})
        previstas.loc[parte.index] = [CLASSES[i] for i in niveis]
    return previstas.to_numpy(dtype=object)


def proporcoes_fora_da_dobra(x, y, peso_vermelho):
    """Proporcoes de cada amostra do treino previstas por uma arvore que nao a viu (validacao cruzada k=5)."""
    dobras = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMENTE)
    proporcoes = np.zeros((len(y), len(CLASSES)))
    for treino, validacao in dobras.split(x, y):
        arvore = nova_arvore(peso_vermelho).fit(x.iloc[treino], y[treino])
        ordem = [list(arvore.classes_).index(c) for c in CLASSES]
        proporcoes[validacao] = arvore.predict_proba(x.iloc[validacao])[:, ordem]
    return proporcoes


def selecionar_decisao(x_trein, y_trein):
    """Escolhe (peso do Vermelho, limiar) por validacao cruzada no treino. Devolve a escolha e a tabela completa."""
    tabela = []
    for peso in PESOS_VERMELHO:
        proporcoes = proporcoes_fora_da_dobra(x_trein, y_trein, peso)
        for limiar in LIMIARES:
            previstas, _ = decidir(proporcoes, CLASSES, limiar)
            r = resumir(y_trein, previstas)
            tabela.append({"peso_vermelho": peso, "limiar_vermelho": limiar,
                           "revocacao_vermelho": r["revocacao_vermelho"],
                           "precisao_vermelho": r["por_classe"]["Vermelho"]["precisao"],
                           "acuracia": r["acuracia"], "f1_macro": r["media_macro"]["f1"]})
    atingem = [linha for linha in tabela if linha["revocacao_vermelho"] >= META_REVOCACAO_VERMELHO]
    if atingem:
        escolha = max(atingem, key=lambda l: (l["f1_macro"], l["limiar_vermelho"] or 1.0, -l["peso_vermelho"]))
    else:
        escolha = max(tabela, key=lambda l: (l["revocacao_vermelho"], l["f1_macro"]))
    return escolha, tabela


def avaliar_no_teste(x_trein, y_trein, x_teste, y_teste, peso, limiar):
    arvore = nova_arvore(peso).fit(x_trein, y_trein)
    ordem = [list(arvore.classes_).index(c) for c in CLASSES]
    previstas, _ = decidir(arvore.predict_proba(x_teste)[:, ordem], CLASSES, limiar)
    return arvore, resumir(y_teste, previstas)


def main(salvar=False):
    sys.stdout.reconfigure(encoding="utf-8")
    quadro = gerar()
    x, y = preparar(quadro), quadro["classe"].to_numpy(dtype=object)
    x_trein, x_teste, y_trein, y_teste = train_test_split(x, y, test_size=0.2, stratify=y, random_state=SEMENTE)

    escolha, tabela_cv = selecionar_decisao(x_trein, y_trein)
    modelo, metricas = avaliar_no_teste(x_trein, y_trein, x_teste, y_teste,
                                        escolha["peso_vermelho"], escolha["limiar_vermelho"])
    # Comparacoes no teste (so para relatar; a escolha acima ja estava feita).
    _, sem_ajuste = avaliar_no_teste(x_trein, y_trein, x_teste, y_teste, 1, None)
    linha_base = resumir(y_teste, DummyClassifier(strategy="most_frequent").fit(x_trein, y_trein).predict(x_teste))
    referencia = resumir(y_teste, regra_sem_ruido(quadro.loc[x_teste.index]))
    # Alternativa so com o limiar (sem peso extra), escolhida pelo mesmo criterio na validacao cruzada.
    candidatas = [l for l in tabela_cv if l["peso_vermelho"] == 1 and l["limiar_vermelho"] is not None]
    atingem = [l for l in candidatas if l["revocacao_vermelho"] >= META_REVOCACAO_VERMELHO]
    so_limiar = (max(atingem, key=lambda l: (l["f1_macro"], l["limiar_vermelho"])) if atingem
                 else max(candidatas, key=lambda l: (l["revocacao_vermelho"], l["f1_macro"])))
    _, teste_so_limiar = avaliar_no_teste(x_trein, y_trein, x_teste, y_teste, 1, so_limiar["limiar_vermelho"])

    def curto(r):
        return {k: r[k] for k in ("acuracia", "media_macro", "revocacao_vermelho", "falsos_negativos_vermelho")} | {
            "precisao_vermelho": r["por_classe"]["Vermelho"]["precisao"], "matriz_confusao": r["matriz_confusao"]}

    metricas.update({
        "classes": CLASSES,
        "algoritmo": f"DecisionTreeClassifier(max_depth={PROFUNDIDADE}, min_samples_leaf={FOLHA_MINIMA})",
        "decisao": {
            "peso_vermelho": escolha["peso_vermelho"], "limiar_vermelho": escolha["limiar_vermelho"],
            "meta_revocacao_vermelho": META_REVOCACAO_VERMELHO,
            "meta_atingida_no_teste": metricas["revocacao_vermelho"] >= META_REVOCACAO_VERMELHO,
            "criterio": ("Validação cruzada estratificada (k=5) só no treino: entre as combinações de peso do Vermelho "
                         "e limiar com revocação do Vermelho >= 0,90, a de maior F1 macro."),
            "validacao_cruzada_escolhida": escolha,
            "validacao_cruzada_todas": tabela_cv,
        },
        "sem_ajuste_conservador": curto(sem_ajuste) | {"descricao": "mesma árvore, sem peso extra e sem limiar"},
        "alternativa_so_limiar": curto(teste_so_limiar) | {
            "limiar_vermelho": so_limiar["limiar_vermelho"], "validacao_cruzada": so_limiar,
            "descricao": "mesma árvore sem peso extra, com o limiar conservador escolhido pelo mesmo critério"},
        "linha_base": {"estrategia": "classe majoritária (DummyClassifier)", "acuracia": linha_base["acuracia"],
                       "media_macro": linha_base["media_macro"],
                       "revocacao_vermelho": linha_base["revocacao_vermelho"]},
        "teto_referencia": curto(referencia) | {
            "descricao": ("A própria regra de rotulagem aplicada às leituras sem ruído, comparada aos rótulos gerados "
                          "com ruído de medição. Serve de referência (teto aproximado) para a acurácia do modelo.")},
        "tamanho_treino": int(len(x_trein)), "tamanho_teste": int(len(x_teste)),
        "divisao": f"80/20 estratificada (train_test_split, random_state={SEMENTE})",
        "origem_dados": "simulado",
        "versao_scikit_learn": sklearn.__version__,
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "aviso": AVISO,
    })

    resumo = {"modelo_escolhido": curto(metricas), "sem_ajuste_conservador": metricas["sem_ajuste_conservador"],
              "alternativa_so_limiar": metricas["alternativa_so_limiar"],
              "teto_referencia": metricas["teto_referencia"], "linha_base": metricas["linha_base"],
              "decisao": {k: v for k, v in metricas["decisao"].items() if k != "validacao_cruzada_todas"}}
    print(json.dumps(resumo, ensure_ascii=False, indent=1))

    if not salvar:
        print("\n(Nada foi gravado. Use --salvar para gravar dataset, modelo.pkl e metricas.json.)")
        return metricas
    PASTA_SAIDA.mkdir(exist_ok=True)
    quadro.to_csv(PASTA_SAIDA / "dataset_simulado.csv", index=False)
    joblib.dump({"modelo": modelo, "atributos": ATRIBUTOS, "classes": list(modelo.classes_),
                 "limiar_vermelho": escolha["limiar_vermelho"], "peso_vermelho": escolha["peso_vermelho"]},
                PASTA_SAIDA / "modelo.pkl")
    (PASTA_SAIDA / "metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nGravado em {PASTA_SAIDA}")
    return metricas


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    argumentos.add_argument("--salvar", action="store_true", help="grava dataset, modelo.pkl e metricas.json")
    main(salvar=argumentos.parse_args().salvar)
