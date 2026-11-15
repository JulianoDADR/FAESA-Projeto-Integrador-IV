"""Avaliacao de uma leitura: o MESMO caminho para /classificar, para o simulador e (Etapa 4) para o banco.

validacao -> classificador (decide a cor) -> camada de explicacao (LLM so reformula; mensagem-padrao se falhar).
"""
from datetime import datetime, timezone

from app import classificador, explicacao, faixas
from app.validacao import CAMPOS, validar_leitura

MENSAGEM_SEM_DADOS = ("Não recebemos leitura recente deste ponto. Confira o sensor e a conexão. "
                      "Nenhuma avaliação é mostrada até chegar uma leitura válida.")


def agora():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def explicar_proporcoes(peso_vermelho):
    texto = "Proporção de amostras de treino parecidas (mesma folha da árvore) em cada classe"
    if peso_vermelho and peso_vermelho != 1:
        texto += f", com cada amostra Vermelha contando {peso_vermelho:g} vezes (peso de segurança do treino)"
    return texto + ". Não é confiança nem certeza do modelo."


def avaliar(corpo, forcar_falha_llm=False):
    """corpo: dicionario com especie e as tres leituras. Levanta ErroValidacao se a leitura for invalida."""
    leitura = validar_leitura(corpo)
    classe, proporcoes, regra_aplicada = classificador.classificar(leitura)
    mensagem, origem = explicacao.gerar_mensagem(classe, leitura, forcar_falha=forcar_falha_llm)
    fora = faixas.fora_da_faixa_de_treino(leitura)
    decisao = classificador.parametros_decisao()
    return {"classe": classe, "rotulo": classificador.ROTULOS[classe],
            "proporcoes": proporcoes, "explicacao_proporcoes": explicar_proporcoes(decisao["peso_vermelho"]),
            "decisao": decisao | {"regra_conservadora_aplicada": regra_aplicada},
            "mensagem": mensagem, "origem_mensagem": origem, "modo_demonstracao": True,
            "origem_dados": "simulado", "atualizado_em": agora(),
            "aviso_fora_da_faixa_de_treino": bool(fora), "variaveis_fora_da_faixa_de_treino": fora}


def sem_dados():
    """Sem leitura valida: nunca ha cor de avaliacao (relatorio, secao 6.2)."""
    return {"classe": None, "rotulo": "Sem dados atualizados", "proporcoes": None, "mensagem": MENSAGEM_SEM_DADOS,
            "origem_mensagem": "padrao", "modo_demonstracao": True, "origem_dados": "simulado",
            "atualizado_em": None}


def avaliar_leitura_de_fonte(leitura, forcar_falha_llm=False):
    """Leitura vinda de uma FonteDeLeituras: junta os dados brutos com a avaliacao (ou o estado sem dados)."""
    if any(leitura.get(campo) is None for campo in CAMPOS):
        return leitura | sem_dados()
    return leitura | avaliar({c: leitura[c] for c in CAMPOS}, forcar_falha_llm) | {"origem_dados": leitura["origem"]}
