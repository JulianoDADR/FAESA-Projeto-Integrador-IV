"""Indicador de disponibilidade de leituras validas (relatorio, Quadro 5: meta >= 95% em 72 h de operacao continua).

Como a API mede: disponibilidade = leituras validas recebidas na janela / leituras esperadas na janela, com
esperadas = horas * 60 / INTERVALO_LEITURA_MIN (um envio por ponto a cada N minutos). Limitada a 100%.

Limite honesto: a API so ve o que chegou. Linhas descartadas no proprio gateway (mensagem incompleta, oscilacao)
aparecem como leituras que faltaram, nao como rejeicoes; o gateway imprime o proprio resumo de descartes.
"""
import os
from datetime import timedelta

from sqlalchemy import func, select

from app import banco
from app.fontes import TALHOES

META_DISPONIBILIDADE = 0.95


def intervalo_leitura_min():
    return float(os.getenv("INTERVALO_LEITURA_MIN", "10"))


def disponibilidade(horas=72, agora=None):
    agora = agora or banco.agora_utc()
    inicio = agora - timedelta(hours=horas)
    intervalo = intervalo_leitura_min()
    esperadas = int(horas * 60 // intervalo)
    por_talhao = []
    with banco.sessao() as s:
        for t in TALHOES:
            validas = s.scalar(select(func.count()).select_from(banco.Leitura).where(
                banco.Leitura.talhao_id == t["id"], banco.Leitura.valida,
                banco.Leitura.coletado_em > inicio, banco.Leitura.coletado_em <= agora))
            rejeitadas = s.scalar(select(func.count()).select_from(banco.Rejeicao).where(
                banco.Rejeicao.talhao_id == t["id"], banco.Rejeicao.recebido_em > inicio,
                banco.Rejeicao.recebido_em <= agora))
            valor = min(1.0, validas / esperadas) if esperadas else 0.0
            por_talhao.append({"talhao_id": t["id"], "validas": validas, "rejeitadas": rejeitadas,
                               "esperadas": esperadas, "disponibilidade": round(valor, 4),
                               "meta_atingida": valor >= META_DISPONIBILIDADE})
    total_validas = sum(p["validas"] for p in por_talhao)
    total_esperadas = esperadas * len(TALHOES)
    geral = min(1.0, total_validas / total_esperadas) if total_esperadas else 0.0
    return {"janela_horas": horas, "intervalo_leitura_min": intervalo, "meta": META_DISPONIBILIDADE,
            "disponibilidade_geral": round(geral, 4), "meta_atingida": geral >= META_DISPONIBILIDADE,
            "por_talhao": por_talhao, "calculado_em": agora.isoformat(),
            "observacao": ("Válidas recebidas ÷ esperadas (um envio por ponto a cada intervalo). Descartes feitos no "
                           "próprio gateway aparecem como leituras que faltaram.")}
