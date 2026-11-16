"""Semente do banco: grava leituras SIMULADAS das ultimas horas para o deploy nao abrir vazio.

Uso (dentro de prototipo/):  python -m app.semear --horas 72

Usa a mesma FonteSimulada das paginas, alinhada ao relogio de Brasilia (a leitura das 15h e a do "15:00" simulado),
uma leitura por talhao a cada INTERVALO_LEITURA_MIN minutos, em uma grade fixa de horarios. Todas com origem =
"simulado". Pode rodar de novo: leituras que ja existem (mesmo talhao e instante) sao ignoradas, mesmo se a execucao
ocorrer minutos depois. Uma nova leitura em um intervalo posterior da grade e permitida.
"""
import argparse
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app import banco
from app.fontes import FUSO_EXIBICAO, MINUTOS_POR_PASSO, TALHOES, FonteSimulada
from app.indicadores import intervalo_leitura_min


def _alinhar_grade(instante, intervalo_minutos):
    """Arredonda para baixo ate o inicio do intervalo (grade fixa em UTC, sem segundos)."""
    instante = instante.astimezone(timezone.utc).replace(second=0, microsecond=0)
    minutos = int(instante.timestamp() // 60)
    resto = minutos % intervalo_minutos
    return instante - timedelta(minutes=resto)


def passo_do_instante(instante):
    """Passo do simulador cuja hora simulada coincide com a hora de Brasilia do instante."""
    local = instante.astimezone(FUSO_EXIBICAO)
    minutos = (local.replace(tzinfo=timezone.utc) - datetime(1970, 1, 1, tzinfo=timezone.utc)).total_seconds() / 60
    return int(minutos // MINUTOS_POR_PASSO)


def semear(horas=72, agora=None, intervalo_min=None):
    intervalo_minutos = int(intervalo_min or intervalo_leitura_min())
    intervalo = timedelta(minutes=intervalo_minutos)
    agora = _alinhar_grade(agora or banco.agora_utc(), intervalo_minutos)
    inicio = agora - timedelta(hours=horas)
    fonte = FonteSimulada()
    gravadas = ignoradas = 0
    with banco.sessao() as s:
        existentes = {(t, c) for t, c in s.execute(select(banco.Leitura.talhao_id, banco.Leitura.coletado_em).where(
            banco.Leitura.coletado_em >= inicio, banco.Leitura.coletado_em <= agora))}
        instante = inicio + intervalo
        while instante <= agora:
            passo = passo_do_instante(instante)
            for talhao in TALHOES:
                leitura = fonte.leitura(talhao["id"], passo)
                if leitura["umidade_solo"] is None:
                    continue  # sensor sem sinal nesse momento: fica o buraco, como na vida real
                if (talhao["id"], instante) in existentes:
                    ignoradas += 1
                    continue
                s.add(banco.Leitura(talhao_id=talhao["id"], especie=talhao["especie"], coletado_em=instante,
                                    recebido_em=agora, origem="simulado", valida=True,
                                    umidade_solo=leitura["umidade_solo"], temperatura=leitura["temperatura"],
                                    umidade_ar=leitura["umidade_ar"]))
                existentes.add((talhao["id"], instante))
                gravadas += 1
            instante += intervalo
        s.commit()
    return {"gravadas": gravadas, "ignoradas": ignoradas, "horas": horas, "intervalo_min": intervalo_minutos}


if __name__ == "__main__":
    argumentos = argparse.ArgumentParser(description="Grava leituras SIMULADAS das últimas horas no banco.")
    argumentos.add_argument("--horas", type=int, default=72)
    opcoes = argumentos.parse_args()
    banco.configurar()
    print(semear(opcoes.horas), "-> banco:", banco.descrever_url())
