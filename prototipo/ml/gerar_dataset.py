"""Gera o conjunto de dados SIMULADO do AgroAnalise (origem = "simulado").

ATENCAO: as faixas abaixo sao PROVISORIAS, de demonstracao. NAO sao parametros
agronomicos validados (relatorio, secao 8.3: a validacao com referencias/ZARC/Embrapa
e etapa posterior). As diferencas entre Arabica e Conilon sao so ilustrativas.

Metodo de rotulagem (documentado):
  1. Cada variavel recebe um nivel segundo sua faixa ideal e sua margem de tolerancia:
       dentro da faixa ideal                  -> 0 (ideal)
       fora, mas dentro da margem             -> 1 (atencao)
       alem da margem                         -> 2 (critico)
  2. A classe da amostra e o PIOR nivel entre as tres variaveis
       0 -> Verde, 1 -> Amarelo, 2 -> Vermelho.
  3. Para o problema nao ser trivial, a rotulagem usa as leituras com um ruido
     gaussiano (incerteza de medicao), mas o conjunto guarda as leituras SEM esse ruido.
     Assim ha sobreposicao perto das fronteiras e o classificador nao chega a 100%.
"""
from pathlib import Path

import numpy as np
import pandas as pd

SEMENTE = 42
NUM_AMOSTRAS = 3000
CLASSES = ["Verde", "Amarelo", "Vermelho"]

# (inicio_ideal, fim_ideal, margem)  -- valores provisorios de demonstracao
FAIXAS = {
    "Arabica": {"umidade_solo": (40, 70, 15), "temperatura": (18, 24, 4), "umidade_ar": (60, 85, 12)},
    "Conilon": {"umidade_solo": (40, 70, 15), "temperatura": (22, 30, 4), "umidade_ar": (60, 85, 12)},
}
# desvio padrao do ruido de rotulagem por variavel
RUIDO = {"umidade_solo": 3.0, "temperatura": 1.0, "umidade_ar": 3.0}
LIMITES = {"umidade_solo": (0, 100), "temperatura": (5, 42), "umidade_ar": (15, 100)}


def nivel_variavel(valor, inicio, fim, margem):
    """0 = ideal, 1 = atencao, 2 = critico (vetorizado)."""
    distancia = np.maximum(np.maximum(inicio - valor, valor - fim), 0)
    return np.where(distancia == 0, 0, np.where(distancia <= margem, 1, 2))


def rotular(especie, leituras):
    niveis = []
    for variavel, (inicio, fim, margem) in FAIXAS[especie].items():
        niveis.append(nivel_variavel(leituras[variavel], inicio, fim, margem))
    return np.max(niveis, axis=0)


def gerar(num_amostras=NUM_AMOSTRAS, semente=SEMENTE):
    gerador = np.random.default_rng(semente)
    partes = []
    for especie in ("Arabica", "Conilon"):
        n = num_amostras // 2
        dados = {}
        # modo de amostragem por linha: 0 = dentro do ideal, 1 = perto do ideal, 2 = faixa ampla.
        # Serve so para equilibrar as classes; nao interfere na regra de rotulagem.
        modo = gerador.choice(3, size=n, p=[0.30, 0.35, 0.35])
        for variavel, (inicio, fim, margem) in FAIXAS[especie].items():
            minimo, maximo = LIMITES[variavel]
            amplo = gerador.uniform(minimo, maximo, n)
            proximo = gerador.uniform(inicio - 1.3 * margem, fim + 1.3 * margem, n)
            dentro = gerador.uniform(inicio, fim, n)
            dados[variavel] = np.clip(np.select([modo == 0, modo == 1], [dentro, proximo], amplo), minimo, maximo)
        ruidosas = {v: dados[v] + gerador.normal(0, RUIDO[v], n) for v in dados}
        quadro = pd.DataFrame({k: np.round(v, 1) for k, v in dados.items()})
        quadro.insert(0, "especie", especie)
        quadro["classe"] = [CLASSES[i] for i in rotular(especie, ruidosas)]
        quadro["origem"] = "simulado"
        partes.append(quadro)
    return pd.concat(partes, ignore_index=True).sample(frac=1, random_state=semente).reset_index(drop=True)


if __name__ == "__main__":
    saida = Path(__file__).parent / "saida"
    saida.mkdir(exist_ok=True)
    quadro = gerar()
    quadro.to_csv(saida / "dataset_simulado.csv", index=False)
    print(f"{len(quadro)} amostras SIMULADAS salvas em {saida / 'dataset_simulado.csv'}")
    print(quadro["classe"].value_counts().to_string())
