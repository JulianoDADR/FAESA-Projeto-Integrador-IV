"""Alimentador de demonstracao: grava no banco, a cada INTERVALO_LEITURA_MIN, uma leitura SIMULADA por talhao.

Serve para a URL publica nunca abrir cinza quando nenhum gateway esta ligado (ALIMENTADOR_DEMO=1). Usa o MESMO
caminho de validacao da ingestao (app/ingestao.registrar) e grava origem = "simulado". Desligue-o quando um gateway
de verdade estiver enviando, para nao misturar as duas fontes.

Plano gratuito: quando o servico "dorme", o alimentador para junto; ao acordar ele grava na hora. O intervalo em que
o servico dormiu aparece como leituras que faltaram no indicador de disponibilidade (que e o comportamento honesto).
"""
import asyncio
import logging
import os
from datetime import timezone

from fastapi.concurrency import run_in_threadpool

from app import banco, ingestao
from app.fontes import TALHOES, FonteSimulada
from app.indicadores import intervalo_leitura_min
from app.semear import passo_do_instante

registro = logging.getLogger("agroanalise.alimentador")
_fonte = FonteSimulada()


def ligado():
    if os.getenv("VERCEL"):  # funcao serverless nao mantem tarefa em segundo plano
        return False
    return os.getenv("ALIMENTADOR_DEMO", "").strip().lower() in ("1", "true", "sim", "yes")


def gravar_agora(agora=None):
    """Uma leitura simulada por talhao no instante atual (arredondado ao minuto). Devolve quantas foram gravadas."""
    agora = (agora or banco.agora_utc()).replace(second=0, microsecond=0)
    passo = passo_do_instante(agora)
    gravadas = 0
    for talhao in TALHOES:
        leitura = _fonte.leitura(talhao["id"], passo)
        if leitura["umidade_solo"] is None:
            continue  # sensor "sem sinal" no simulador: nada e enviado, como faria o Arduino
        corpo = {"talhao_id": talhao["id"], "coletado_em": agora.astimezone(timezone.utc).isoformat(),
                 "umidade_solo": leitura["umidade_solo"], "temperatura": leitura["temperatura"],
                 "umidade_ar": leitura["umidade_ar"], "origem": "simulado"}
        situacao, _ = ingestao.registrar(corpo, agora=banco.agora_utc())
        gravadas += situacao == 201
    return gravadas


async def laco():
    intervalo_s = intervalo_leitura_min() * 60
    registro.info("Alimentador de demonstração ligado: uma leitura simulada por talhão a cada %.0f s.", intervalo_s)
    while True:
        try:
            gravadas = await run_in_threadpool(gravar_agora)
            registro.info("Alimentador gravou %d leituras simuladas.", gravadas)
        except Exception:  # nunca derruba a API por causa da demonstracao
            registro.exception("Falha no alimentador de demonstração")
        await asyncio.sleep(intervalo_s)
