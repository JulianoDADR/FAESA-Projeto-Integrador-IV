"""Ingestao de leituras enviadas pelo gateway (POST /leituras), relatorio secoes 8.2, 8.4 e 10.2.

- Autenticacao por token de dispositivo (Authorization: Bearer <TOKEN_DISPOSITIVO>), comparado em tempo constante.
- So campos estruturados e conhecidos; campos extras sao recusados (como em /classificar).
- Valores fora do fisicamente possivel sao recusados e contados como rejeicao (indicador de disponibilidade).
- Idempotencia por (talhao, instante de coleta): reenviar a mesma leitura nao duplica; mesma chave com valores
  diferentes e conflito (409).
"""
import hmac
import math
import os
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app import banco
from app.fontes import TALHOES
from app.validacao import ErroValidacao, validar_leitura

CAMPOS = ("talhao_id", "coletado_em", "umidade_solo", "temperatura", "umidade_ar", "origem")
ORIGENS = ("simulado", "dispositivo")
VARIAVEIS = ("umidade_solo", "temperatura", "umidade_ar")
TOLERANCIA_FUTURO = timedelta(minutes=5)
IDADE_MAXIMA = timedelta(days=30)
ESPECIE_DO_TALHAO = {t["id"]: t["especie"] for t in TALHOES}  # cadastro dos pontos (a especie nao vem do dispositivo)


class ErroIngestao(Exception):
    def __init__(self, status, erros):
        super().__init__("; ".join(erros))
        self.status, self.erros = status, erros


def token_configurado():
    return bool(os.getenv("TOKEN_DISPOSITIVO"))


def verificar_token(cabecalho):
    esperado = os.getenv("TOKEN_DISPOSITIVO")
    if not esperado:
        raise ErroIngestao(503, ["Recebimento de leituras desligado: defina TOKEN_DISPOSITIVO no servidor."])
    if not cabecalho or not cabecalho.startswith("Bearer "):
        raise ErroIngestao(401, ["Falta o token do dispositivo (Authorization: Bearer ...)."])
    if not hmac.compare_digest(cabecalho[len("Bearer "):].encode(), esperado.encode()):
        raise ErroIngestao(401, ["Token do dispositivo inválido."])


def _ler_instante(texto, agora):
    if not isinstance(texto, str):
        raise ErroIngestao(422, ["coletado_em precisa ser data e hora no formato ISO 8601."])
    try:
        instante = datetime.fromisoformat(texto.replace("Z", "+00:00"))
    except ValueError:
        raise ErroIngestao(422, ["coletado_em precisa ser data e hora no formato ISO 8601."])
    if instante.tzinfo is None:
        raise ErroIngestao(422, ["coletado_em precisa ter fuso horário (ex.: 2026-11-15T10:00:00-03:00)."])
    if instante > agora + TOLERANCIA_FUTURO:
        raise ErroIngestao(422, ["coletado_em está no futuro. Confira o relógio do gateway."])
    if instante < agora - IDADE_MAXIMA:
        raise ErroIngestao(422, ["coletado_em é antigo demais (mais de 30 dias)."])
    return instante


def validar_corpo(corpo, agora):
    """Checagem estrutural. Devolve (talhao_id, instante, origem, valores) ou levanta ErroIngestao."""
    if not isinstance(corpo, dict):
        raise ErroIngestao(422, ["Envie a leitura em formato de objeto JSON."])
    extras = sorted(str(k) for k in corpo if k not in CAMPOS)
    if extras:
        raise ErroIngestao(422, ["Campo não permitido: " + ", ".join(extras) + "."])
    faltando = [c for c in CAMPOS if corpo.get(c) is None]
    if faltando:
        raise ErroIngestao(422, ["Falta informar: " + ", ".join(faltando) + "."])
    talhao_id = corpo["talhao_id"]
    if talhao_id not in ESPECIE_DO_TALHAO:
        raise ErroIngestao(422, [f"Ponto de monitoramento desconhecido: {talhao_id}."])
    if corpo["origem"] not in ORIGENS:
        raise ErroIngestao(422, ["origem precisa ser 'simulado' ou 'dispositivo'."])
    for v in VARIAVEIS:
        valor = corpo[v]
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or not math.isfinite(valor):
            raise ErroIngestao(422, [f"{v} precisa ser um número."])
    return talhao_id, _ler_instante(corpo["coletado_em"], agora), corpo["origem"], {v: float(corpo[v]) for v in VARIAVEIS}


def registrar(corpo, agora=None):
    """Valida e grava. Devolve (status_http, resposta)."""
    agora = agora or banco.agora_utc()
    talhao_id, instante, origem, valores = validar_corpo(corpo, agora)
    especie = ESPECIE_DO_TALHAO[talhao_id]
    try:
        validar_leitura({"especie": especie, **valores})  # mesmos limites fisicos da API de classificacao
    except ErroValidacao as erro:
        with banco.sessao() as s:
            s.add(banco.Rejeicao(talhao_id=talhao_id, recebido_em=agora, motivo="; ".join(erro.erros)[:300]))
            s.commit()
        raise ErroIngestao(422, erro.erros)

    with banco.sessao() as s:
        s.add(banco.Leitura(talhao_id=talhao_id, especie=especie, coletado_em=instante, recebido_em=agora,
                            origem=origem, valida=True, **valores))
        try:
            s.commit()
        except IntegrityError:
            s.rollback()
            existente = s.scalars(select(banco.Leitura).where(banco.Leitura.talhao_id == talhao_id,
                                                              banco.Leitura.coletado_em == instante)).one()
            iguais = all(math.isclose(getattr(existente, v), valores[v], abs_tol=1e-9) for v in VARIAVEIS)
            if not iguais:
                raise ErroIngestao(409, ["Já existe outra leitura deste ponto neste mesmo instante, com valores diferentes."])
            return 200, {"situacao": "duplicada", "id": existente.id}
        return 201, {"situacao": "gravada", "talhao_id": talhao_id, "especie": especie,
                     "coletado_em": instante.isoformat()}
