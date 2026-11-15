"""Avaliacao (eval) do classificador do AgroAnalise. Gera docs/avaliacao/classificador.json e .md.

Uso (dentro de prototipo/):  python ml/avaliar_classificador.py

Metodo (relatorio, secoes 5.5, 5.6 e 7.4):
  1. Mesma divisao 80/20 estratificada do treino (random_state=42). O conjunto de teste so e usado no passo 4.
  2. Validacao cruzada estratificada k=5 NO TREINO, com media e desvio, para cada combinacao de uma busca pequena:
     profundidade, folha minima, peso do Vermelho (class_weight) e limiar conservador do Vermelho.
  3. Escolha pelo mesmo criterio do treino: maior F1 macro entre as combinacoes com revocacao media do
     Vermelho >= 0,90 na validacao cruzada.
  4. Teste, uma vez: modelo escolhido, modelo em producao (ml/saida/modelo.pkl), linha de base (classe majoritaria)
     e regra de referencia (a propria regra de rotulagem sem ruido). Revocacao do Vermelho com intervalo de Wilson 95%.

Vazamento: o dataset e de amostras independentes (sorteadas uma a uma, sem sequencia no tempo), entao nao ha
sequencias semelhantes para separar por bloco. As leituras do simulador ao vivo NAO sao usadas no treino.
"""
import itertools
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.tree import DecisionTreeClassifier

from gerar_dataset import CLASSES, gerar
from treinar import AVISO, SEMENTE, preparar, regra_sem_ruido, resumir

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from app.decisao import decidir  # noqa: E402

SAIDA = RAIZ.parent / "docs" / "avaliacao"
META = 0.90
GRADE = {
    "profundidade": [4, 6, 8, 10, 12],
    "folha_minima": [1, 5, 10],
    "peso_vermelho": [1, 2, 3, 4],
    "limiar_vermelho": [None, 0.4, 0.3, 0.2],
}


def arvore(profundidade, folha_minima, peso_vermelho):
    pesos = None if peso_vermelho == 1 else {"Verde": 1, "Amarelo": 1, "Vermelho": peso_vermelho}
    return DecisionTreeClassifier(max_depth=profundidade, min_samples_leaf=folha_minima, class_weight=pesos,
                                  random_state=SEMENTE)


def proporcoes(modelo, x):
    ordem = [list(modelo.classes_).index(c) for c in CLASSES]
    return modelo.predict_proba(x)[:, ordem]


def wilson(acertos, total, z=1.96):
    """Intervalo de confianca de Wilson (95%) para uma proporcao."""
    if total == 0:
        return [0.0, 0.0]
    p = acertos / total
    centro = (p + z * z / (2 * total)) / (1 + z * z / total)
    margem = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return [round(centro - margem, 4), round(centro + margem, 4)]


def detalhar(r):
    """Resumo com falsos negativos criticos separados e intervalo da revocacao do Vermelho."""
    m = r["matriz_confusao"]
    vermelhos = sum(m[2])
    return {
        "acuracia": r["acuracia"], "f1_macro": r["media_macro"]["f1"], "media_macro": r["media_macro"],
        "por_classe": r["por_classe"], "matriz_confusao": m,
        "revocacao_vermelho": r["revocacao_vermelho"],
        "revocacao_vermelho_ic95": wilson(m[2][2], vermelhos),
        "precisao_vermelho": r["por_classe"]["Vermelho"]["precisao"],
        "falsos_negativos_criticos": {"vermelho_como_amarelo": m[2][1], "vermelho_como_verde": m[2][0],
                                      "total": m[2][0] + m[2][1], "de_vermelhos": vermelhos},
        "falsos_alarmes_vermelho": {"amarelo_como_vermelho": m[1][2], "verde_como_vermelho": m[0][2]},
    }


def validacao_cruzada(x, y):
    """Para cada combinacao da grade: media e desvio das metricas nas 5 dobras (so no treino)."""
    dobras = list(StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMENTE).split(x, y))
    linhas = []
    for prof, folha, peso in itertools.product(GRADE["profundidade"], GRADE["folha_minima"], GRADE["peso_vermelho"]):
        por_dobra = []
        for treino, validacao in dobras:
            modelo = arvore(prof, folha, peso).fit(x.iloc[treino], y[treino])
            por_dobra.append(proporcoes(modelo, x.iloc[validacao]))
        for limiar in GRADE["limiar_vermelho"]:
            valores = {"revocacao_vermelho": [], "precisao_vermelho": [], "acuracia": [], "f1_macro": []}
            for (_, validacao), props in zip(dobras, por_dobra):
                previstas, _ = decidir(props, CLASSES, limiar)
                r = resumir(y[validacao], previstas)
                valores["revocacao_vermelho"].append(r["revocacao_vermelho"])
                valores["precisao_vermelho"].append(r["por_classe"]["Vermelho"]["precisao"])
                valores["acuracia"].append(r["acuracia"])
                valores["f1_macro"].append(r["media_macro"]["f1"])
            linha = {"profundidade": prof, "folha_minima": folha, "peso_vermelho": peso, "limiar_vermelho": limiar}
            for chave, lista in valores.items():
                linha[chave] = round(float(np.mean(lista)), 4)
                linha[chave + "_desvio"] = round(float(np.std(lista)), 4)
            linhas.append(linha)
    return linhas


def escolher(linhas):
    atingem = [l for l in linhas if l["revocacao_vermelho"] >= META]
    if atingem:
        return max(atingem, key=lambda l: (l["f1_macro"], l["limiar_vermelho"] or 1.0, -l["profundidade"])), True
    return max(linhas, key=lambda l: (l["revocacao_vermelho"], l["f1_macro"])), False


def efeito_do_limiar(x_trein, y_trein, x_teste, y_teste, prof, folha):
    """Efeito do limiar conservador (sem peso extra) no teste, para o relatorio. Nao e usado para escolher nada."""
    modelo = arvore(prof, folha, 1).fit(x_trein, y_trein)
    props = proporcoes(modelo, x_teste)
    tabela = []
    for limiar in [None, 0.5, 0.4, 0.3, 0.2, 0.15, 0.1]:
        r = resumir(y_teste, decidir(props, CLASSES, limiar)[0])
        tabela.append({"limiar_vermelho": limiar, "revocacao_vermelho": r["revocacao_vermelho"],
                       "precisao_vermelho": r["por_classe"]["Vermelho"]["precisao"], "acuracia": r["acuracia"],
                       "f1_macro": r["media_macro"]["f1"]})
    return tabela


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    quadro = gerar()
    x, y = preparar(quadro), quadro["classe"].to_numpy(dtype=object)
    x_trein, x_teste, y_trein, y_teste = train_test_split(x, y, test_size=0.2, stratify=y, random_state=SEMENTE)

    linhas = validacao_cruzada(x_trein, y_trein)
    escolha, atingiu = escolher(linhas)
    print(f"{len(linhas)} combinações avaliadas por validação cruzada (k=5) no treino.")

    # Teste, uma vez
    modelo = arvore(escolha["profundidade"], escolha["folha_minima"], escolha["peso_vermelho"]).fit(x_trein, y_trein)
    escolhido = detalhar(resumir(y_teste, decidir(proporcoes(modelo, x_teste), CLASSES, escolha["limiar_vermelho"])[0]))
    pacote = joblib.load(RAIZ / "ml" / "saida" / "modelo.pkl")
    em_producao = detalhar(resumir(y_teste, decidir(proporcoes(pacote["modelo"], x_teste[pacote["atributos"]]),
                                                    CLASSES, pacote.get("limiar_vermelho"))[0]))
    producao_params = {"profundidade": pacote["modelo"].max_depth, "folha_minima": pacote["modelo"].min_samples_leaf,
                       "peso_vermelho": pacote.get("peso_vermelho", 1), "limiar_vermelho": pacote.get("limiar_vermelho")}
    producao_cv = next(l for l in linhas if all(l[k] == v for k, v in producao_params.items()))
    linha_base = detalhar(resumir(y_teste, DummyClassifier(strategy="most_frequent").fit(x_trein, y_trein).predict(x_teste)))
    referencia = detalhar(resumir(y_teste, regra_sem_ruido(quadro.loc[x_teste.index])))

    resultado = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "comando": "python ml/avaliar_classificador.py",
        "versao_scikit_learn": sklearn.__version__,
        "origem_dados": "simulado", "aviso": AVISO,
        "dados": {"amostras": int(len(quadro)), "treino": int(len(x_trein)), "teste": int(len(x_teste)),
                  "classes_teste": {c: int((y_teste == c).sum()) for c in CLASSES},
                  "divisao": "80/20 estratificada (random_state=42); validação cruzada estratificada k=5 só no treino"},
        "busca": {"grade": GRADE, "combinacoes": len(linhas), "criterio": (
            "maior F1 macro entre as combinações com revocação média do Vermelho >= 0,90 na validação cruzada"),
                  "meta_atingida_na_validacao_cruzada": atingiu},
        "escolhido": {"parametros": {k: escolha[k] for k in ("profundidade", "folha_minima", "peso_vermelho", "limiar_vermelho")},
                      "validacao_cruzada": escolha, "teste": escolhido},
        "em_producao": {"parametros": producao_params, "validacao_cruzada": producao_cv, "teste": em_producao},
        "linha_base": {"descricao": "classe majoritária (DummyClassifier)", "teste": linha_base},
        "regra_de_referencia": {"descricao": "a própria regra de rotulagem aplicada às leituras sem ruído (teto aproximado)",
                                "teste": referencia},
        "efeito_do_limiar_no_teste": efeito_do_limiar(x_trein, y_trein, x_teste, y_teste,
                                                      producao_params["profundidade"], producao_params["folha_minima"]),
        "melhores_na_validacao_cruzada": sorted(linhas, key=lambda l: -l["f1_macro"])[:10],
        "vazamento": ("Amostras independentes, sem sequência temporal: não há blocos a separar. As leituras do "
                      "simulador ao vivo não entram no treino."),
    }
    SAIDA.mkdir(parents=True, exist_ok=True)
    (SAIDA / "classificador.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    (SAIDA / "classificador.md").write_text(relatorio_md(resultado), encoding="utf-8")
    for nome, chave in (("escolhido", "escolhido"), ("em produção", "em_producao")):
        t = resultado[chave]["teste"]
        print(f"{nome:12} {resultado[chave]['parametros']}: acurácia {t['acuracia']}, F1 macro {t['f1_macro']}, "
              f"revocação Vermelho {t['revocacao_vermelho']} IC95 {t['revocacao_vermelho_ic95']}")
    print(f"Relatórios em {SAIDA}")
    return resultado


def _pct(x):
    return f"{x * 100:.1f}%".replace(".", ",")


def _num(x, casas=3):
    return f"{x:.{casas}f}".replace(".", ",")


def _limiar(x):
    return "sem limiar" if x is None else _num(x, 2)


def relatorio_md(r):
    esc, prod = r["escolhido"], r["em_producao"]
    linhas_tabela = []
    for nome, bloco in (("Modelo escolhido nesta avaliação", esc["teste"]), ("Modelo em produção", prod["teste"]),
                        ("Regra de referência (teto)", r["regra_de_referencia"]["teste"]),
                        ("Linha de base (classe majoritária)", r["linha_base"]["teste"])):
        ic = bloco["revocacao_vermelho_ic95"]
        fn = bloco["falsos_negativos_criticos"]
        linhas_tabela.append(
            f"| {nome} | {_num(bloco['acuracia'])} | {_num(bloco['f1_macro'])} | {_num(bloco['revocacao_vermelho'])} "
            f"({_num(ic[0])} a {_num(ic[1])}) | {_num(bloco['precisao_vermelho'])} | {fn['vermelho_como_amarelo']} / "
            f"{fn['vermelho_como_verde']} |")
    m = esc["teste"]["matriz_confusao"]
    limiar = "\n".join(f"| {_limiar(l['limiar_vermelho'])} | {_num(l['revocacao_vermelho'])} | {_num(l['precisao_vermelho'])} | "
                       f"{_num(l['acuracia'])} | {_num(l['f1_macro'])} |" for l in r["efeito_do_limiar_no_teste"])
    top = "\n".join(f"| {l['profundidade']} | {l['folha_minima']} | {l['peso_vermelho']} | {_limiar(l['limiar_vermelho'])} | "
                    f"{_num(l['f1_macro'])} ± {_num(l['f1_macro_desvio'])} | {_num(l['revocacao_vermelho'])} ± "
                    f"{_num(l['revocacao_vermelho_desvio'])} | {_num(l['acuracia'])} ± {_num(l['acuracia_desvio'])} |"
                    for l in r["melhores_na_validacao_cruzada"])
    cv_esc, cv_prod = esc["validacao_cruzada"], prod["validacao_cruzada"]
    return f"""# Avaliação do classificador

> **{r['aviso']}** Todos os dados são **simulados**; as faixas de rotulagem são provisórias.

Gerado por `{r['comando']}` em {r['gerado_em']} (scikit-learn {r['versao_scikit_learn']}).
Números reais da execução; nada foi ajustado à mão.

## Método

- {r['dados']['amostras']} amostras simuladas; {r['dados']['divisao']}.
  Teste: {r['dados']['teste']} amostras ({', '.join(f'{c} {n}' for c, n in r['dados']['classes_teste'].items())}).
- Busca pequena de hiperparâmetros ({r['busca']['combinacoes']} combinações de profundidade, folha mínima, peso do
  Vermelho e limiar conservador), cada uma avaliada pela média de 5 dobras **só no treino**.
- Critério de escolha: {r['busca']['criterio']}.
- O conjunto de teste foi usado **uma vez**, depois da escolha. A revocação do Vermelho tem intervalo de confiança
  de Wilson de 95%.
- Vazamento: {r['vazamento']}

## Resultado no conjunto de teste

| Modelo | Acurácia | F1 macro | Revocação do Vermelho (IC 95%) | Precisão do Vermelho | Vermelho perdido como Amarelo / Verde |
|---|---|---|---|---|---|
{chr(10).join(linhas_tabela)}

- **Escolhido nesta avaliação:** profundidade {esc['parametros']['profundidade']}, folha mínima
  {esc['parametros']['folha_minima']}, peso do Vermelho {esc['parametros']['peso_vermelho']},
  {_limiar(esc['parametros']['limiar_vermelho'])}. Na validação cruzada: F1 macro {_num(cv_esc['f1_macro'])} ±
  {_num(cv_esc['f1_macro_desvio'])}, revocação do Vermelho {_num(cv_esc['revocacao_vermelho'])} ±
  {_num(cv_esc['revocacao_vermelho_desvio'])}.
- **Em produção** (`ml/saida/modelo.pkl`): profundidade {prod['parametros']['profundidade']}, folha mínima
  {prod['parametros']['folha_minima']}, peso do Vermelho {prod['parametros']['peso_vermelho']},
  {_limiar(prod['parametros']['limiar_vermelho'])}. Na validação cruzada: F1 macro {_num(cv_prod['f1_macro'])} ±
  {_num(cv_prod['f1_macro_desvio'])}, revocação do Vermelho {_num(cv_prod['revocacao_vermelho'])} ±
  {_num(cv_prod['revocacao_vermelho_desvio'])}.

Matriz de confusão do modelo escolhido (linhas = real, colunas = previsto; ordem Verde, Amarelo, Vermelho):

| | Verde | Amarelo | Vermelho |
|---|---|---|---|
| **Verde** | {m[0][0]} | {m[0][1]} | {m[0][2]} |
| **Amarelo** | {m[1][0]} | {m[1][1]} | {m[1][2]} |
| **Vermelho** | {m[2][0]} | {m[2][1]} | {m[2][2]} |

## Qual modelo fica em produção

O modelo em produção foi fixado na Etapa 1, **antes** desta avaliação, também por validação cruzada só no treino
(com a profundidade fixa em 8). A busca maior desta avaliação escolheu outra configuração, que atinge a meta na
validação cruzada por margem pequena (revocação do Vermelho {_num(cv_esc['revocacao_vermelho'])} ±
{_num(cv_esc['revocacao_vermelho_desvio'])}) e ficou em {_num(esc['teste']['revocacao_vermelho'])} no teste.
Trocar o modelo agora **olhando estes números de teste** seria escolher pelo teste, o que o método proíbe.
Por isso o modelo em produção **não foi trocado automaticamente**. Os dois intervalos de confiança se sobrepõem;
qualquer troca deve ser decidida pelo grupo com base na validação cruzada (por exemplo, preferindo uma margem maior
sobre a meta), e então reavaliada num conjunto de teste novo.

## Efeito do limiar conservador (sem peso extra, no teste; só para leitura, não usado na escolha)

| Limiar do Vermelho | Revocação do Vermelho | Precisão do Vermelho | Acurácia | F1 macro |
|---|---|---|---|---|
{limiar}

## As 10 melhores combinações por F1 macro na validação cruzada (média ± desvio das 5 dobras)

| Profundidade | Folha mínima | Peso do Vermelho | Limiar | F1 macro | Revocação do Vermelho | Acurácia |
|---|---|---|---|---|---|---|
{top}

## Limitações

- **Rótulos por regra:** os rótulos foram gerados por regras sobre as mesmas variáveis de entrada, com ruído de
  medição. A regra de referência (sem ML) é o teto aproximado; o modelo só pode reaprender a regra. **Isto valida o
  pipeline, não a eficácia agronômica em campo.**
- **Dados simulados e faixas provisórias:** não representam lavouras reais nem parâmetros validados (ZARC, Embrapa).
- **Um único sorteio do dataset e uma única divisão de teste:** o desvio na validação cruzada e o intervalo de
  Wilson dão a ordem de grandeza da incerteza, não cobrem dados reais.
- **Variáveis ausentes:** precipitação, radiação, estágio fenológico, textura do solo e profundidade das raízes não
  entram no modelo (relatório, seção 10.3).
"""


if __name__ == "__main__":
    main()
