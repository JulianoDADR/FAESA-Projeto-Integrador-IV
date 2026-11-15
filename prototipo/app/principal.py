"""API do AgroAnalise (prototipo, dados SIMULADOS). Tambem serve as paginas de ../web.

Subir: uvicorn app.principal:app
"""
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import classificador, explicacao, faixas
from app.validacao import ErroValidacao, validar_leitura

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

app = FastAPI(title="AgroAnálise (protótipo)", description="Dados simulados, modo demonstração.")

CENARIOS = [
    {"id": "ideal", "nome": "Ideal", "especie": "Arabica", "umidade_solo": 55, "temperatura": 21, "umidade_ar": 72},
    {"id": "solo_seco", "nome": "Solo seco", "especie": "Arabica", "umidade_solo": 33, "temperatura": 22, "umidade_ar": 70},
    {"id": "calor_excessivo", "nome": "Calor excessivo", "especie": "Conilon", "umidade_solo": 50, "temperatura": 38, "umidade_ar": 65},
    {"id": "muito_seco", "nome": "Solo muito seco", "especie": "Conilon", "umidade_solo": 12, "temperatura": 31, "umidade_ar": 50},
    {"id": "sem_dados", "nome": "Sem dados", "especie": "Arabica", "umidade_solo": None, "temperatura": None, "umidade_ar": None},
]


def agora():
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


@app.get("/saude")
def saude():
    return {"estado": "ok", "modelo_carregado": classificador.modelo_disponivel(),
            "llm_configurado": explicacao.llm_configurado(), "modo_demonstracao": True}


@app.post("/classificar")
async def classificar(requisicao: Request, simular_falha_llm: bool = False):
    try:
        corpo = await requisicao.json()
    except ValueError:
        return JSONResponse(status_code=422, content={"erros": ["O corpo da requisição não é um JSON válido."]})
    try:
        leitura = validar_leitura(corpo)
    except ErroValidacao as erro:
        return JSONResponse(status_code=422, content={"erros": erro.erros})
    classe, probabilidades = classificador.classificar(leitura)
    # A chamada ao LLM e sincrona (httpx, ate 5 s): roda no pool de threads para nao travar o servidor.
    # Mantemos a rota async para ler o JSON manualmente e devolver erros em portugues simples.
    mensagem, origem = await run_in_threadpool(
        explicacao.gerar_mensagem, classe, leitura, forcar_falha=simular_falha_llm)
    fora = faixas.fora_da_faixa_de_treino(leitura)
    return {"classe": classe, "rotulo": classificador.ROTULOS[classe], "probabilidades": probabilidades,
            "mensagem": mensagem, "origem_mensagem": origem, "modo_demonstracao": True,
            "origem_dados": "simulado", "atualizado_em": agora(),
            "aviso_fora_da_faixa_de_treino": bool(fora), "variaveis_fora_da_faixa_de_treino": fora}


@app.get("/faixas")
def obter_faixas():
    """Faixas provisorias, limites fisicos e intervalo de treino (a interface limita os controles por aqui)."""
    return faixas.carregar_faixas()


@app.get("/metricas")
def metricas():
    caminho = RAIZ / "ml" / "saida" / "metricas.json"
    if not caminho.exists():
        return JSONResponse(status_code=404, content={"erros": ["Métricas não geradas. Rode: python ml/treinar.py"]})
    return json.loads(caminho.read_text(encoding="utf-8"))


@app.get("/cenarios")
def cenarios():
    return CENARIOS


@app.get("/historico")
def historico():
    """24 leituras horarias SIMULADAS (seed fixa), classificadas pelo modelo (sem LLM)."""
    gerador = np.random.default_rng(7)
    fim = datetime.now(timezone.utc).astimezone().replace(minute=0, second=0, microsecond=0)
    solo, pontos = 58.0, []
    for i in range(24):
        solo = float(np.clip(solo - gerador.uniform(0.5, 2.5) + (9 if i == 15 else 0), 5, 95))
        hora = fim - timedelta(hours=23 - i)
        temperatura = 20 + 4 * np.sin((hora.hour - 9) / 24 * 2 * np.pi) + gerador.normal(0, 0.6)
        leitura = {"especie": "Arabica", "umidade_solo": round(solo, 1), "temperatura": round(float(temperatura), 1),
                   "umidade_ar": round(float(np.clip(78 - 1.5 * (temperatura - 18) + gerador.normal(0, 2), 30, 99)), 1)}
        classe, _ = classificador.classificar(leitura)
        pontos.append({**leitura, "hora": hora.isoformat(timespec="minutes"), "classe": classe,
                       "rotulo": classificador.ROTULOS[classe], "origem": "simulado"})
    return pontos


# Paginas estaticas por ultimo, para nao esconder as rotas da API.
app.mount("/", StaticFiles(directory=RAIZ / "web", html=True), name="web")
