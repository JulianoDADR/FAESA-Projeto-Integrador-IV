"""Regra de decisao do semaforo a partir das proporcoes da arvore (usada no treino e na API).

Regra conservadora: se a proporcao de amostras parecidas da classe Vermelho for >= limiar, a classe e Vermelho,
mesmo que outra classe tenha proporcao maior. Isso troca falsos alarmes por menos casos criticos perdidos
(relatorio, secao 7.4). O limiar e escolhido por validacao cruzada no treino, nunca no conjunto de teste.
"""
import numpy as np

CLASSE_CRITICA = "Vermelho"


def decidir(proporcoes, classes, limiar_vermelho):
    """proporcoes: matriz (n, k) na ordem de `classes`. Devolve (classes previstas, regra_aplicada por linha).

    limiar_vermelho=None desliga a regra (vale a maior proporcao; em empate, a primeira classe em `classes`).
    Note que 0,5 NAO e neutro: em folhas 50/50 ele desempata a favor do Vermelho.
    """
    proporcoes = np.asarray(proporcoes, dtype=float)
    classes = np.asarray(classes, dtype=object)
    pela_maior = classes[proporcoes.argmax(axis=1)]
    if limiar_vermelho is None:
        return pela_maior.astype(object), np.zeros(len(pela_maior), dtype=bool)
    indice_critico = list(classes).index(CLASSE_CRITICA)
    pelo_limiar = proporcoes[:, indice_critico] >= limiar_vermelho
    previstas = np.where(pelo_limiar, CLASSE_CRITICA, pela_maior).astype(object)
    regra_aplicada = pelo_limiar & (pela_maior != CLASSE_CRITICA)
    return previstas, regra_aplicada
