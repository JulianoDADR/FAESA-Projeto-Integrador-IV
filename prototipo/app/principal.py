"""API do AgroAnalise (prototipo, dados SIMULADOS). Tambem serve as paginas de ../web.

Subir: uvicorn app.principal:app
"""
import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app import banco, classificador, explicacao, faixas, fontes, indicadores, ingestao, servico
from app.validacao import ErroValidacao

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

@asynccontextmanager
async def ciclo_de_vida(_app):
    banco.configurar()  # cria as tabelas se ainda nao existirem (migracao simples)
    yield


app = FastAPI(title="AgroAnálise (protótipo)", description="Dados simulados, modo demonstração.", lifespan=ciclo_de_vida)

CENARIOS = [
    {"id": "ideal", "nome": "Ideal", "especie": "Arabica", "umidade_solo": 55, "temperatura": 21, "umidade_ar": 72},
    {"id": "solo_seco", "nome": "Solo seco", "especie": "Arabica", "umidade_solo": 33, "temperatura": 22, "umidade_ar": 70},
    {"id": "calor_excessivo", "nome": "Calor excessivo", "especie": "Conilon", "umidade_solo": 50, "temperatura": 38, "umidade_ar": 65},
    {"id": "muito_seco", "nome": "Solo muito seco", "especie": "Conilon", "umidade_solo": 12, "temperatura": 31, "umidade_ar": 50},
    {"id": "sem_dados", "nome": "Sem dados", "especie": "Arabica", "umidade_solo": None, "temperatura": None, "umidade_ar": None},
]


@app.get("/saude")
def saude():
    return {"estado": "ok", "modelo_carregado": classificador.modelo_disponivel(),
            "llm_configurado": explicacao.llm_configurado(), "modo_demonstracao": True,
            "fonte_leituras": fontes.fonte_ativa().nome, "banco": banco.descrever_url(),
            "recebimento_leituras_ligado": ingestao.token_configurado()}


@app.post("/classificar")
async def classificar(requisicao: Request, simular_falha_llm: bool = False):
    try:
        corpo = await requisicao.json()
    except ValueError:
        return JSONResponse(status_code=422, content={"erros": ["O corpo da requisição não é um JSON válido."]})
    try:
        # A chamada ao LLM e sincrona (httpx, ate 5 s): roda no pool de threads para nao travar o servidor.
        # Mantemos a rota async para ler o JSON manualmente e devolver erros em portugues simples.
        return await run_in_threadpool(servico.avaliar, corpo, simular_falha_llm)
    except ErroValidacao as erro:
        return JSONResponse(status_code=422, content={"erros": erro.erros})


@app.get("/faixas")
def obter_faixas():
    """Faixas provisorias, limites fisicos e intervalo de treino (a interface limita os controles por aqui)."""
    return faixas.carregar_faixas()


@app.get("/metricas")
def metricas():
    caminho = RAIZ / "ml" / "saida" / "metricas.json"
    if not caminho.exists():
        return JSONResponse(status_code=404,
                            content={"erros": ["Métricas não geradas. Rode: python ml/treinar.py --salvar"]})
    return json.loads(caminho.read_text(encoding="utf-8"))


@app.get("/cenarios")
def cenarios():
    return CENARIOS


SIMULADOR = fontes.FonteSimulada()


def _talhao_existe(talhao):
    return any(t["id"] == talhao for t in fontes.fonte_ativa().talhoes())


@app.get("/talhoes")
def talhoes():
    fonte = fontes.fonte_ativa()
    return {"fonte": fonte.nome, "origem_dados": fonte.origem, "talhoes": fonte.talhoes()}


def _montar_status(fonte, talhao, passo, simular_falha_llm):
    if talhao is not None and not _talhao_existe(talhao):
        return JSONResponse(status_code=404, content={"erros": [f"Talhão desconhecido: {talhao}."]})
    simulada = isinstance(fonte, fontes.FonteSimulada)
    passo = (fontes.passo_atual() if passo is None else passo) if simulada else None
    leituras = [l for l in fonte.leituras(passo) if talhao is None or l["talhao_id"] == talhao]
    nomes = {t["id"]: t for t in fonte.talhoes()}
    corpo = {"fonte": fonte.nome, "origem_dados": fonte.origem, "propriedade": fontes.PROPRIEDADE,
             "modo_demonstracao": True, "gerado_em": servico.agora(), "passo": passo,
             "leituras": [nomes[l["talhao_id"]] | servico.avaliar_leitura_de_fonte(l, simular_falha_llm)
                          for l in leituras]}
    if simulada:
        corpo |= {"passo_relogio": fontes.passo_atual(), "hora_simulada": fontes.hora_simulada(passo),
                  "segundos_por_passo": fontes.SEGUNDOS_POR_PASSO, "minutos_por_passo": fontes.MINUTOS_POR_PASSO}
    else:
        corpo |= {"minutos_desatualizado": fonte.minutos_desatualizado}
    return corpo


@app.get("/status")
def status(talhao: str | None = None, passo: int | None = Query(None, ge=0), simular_falha_llm: bool = False):
    """Estado atual de cada talhao, vindo da fonte ativa (FONTE_LEITURAS). As paginas usam esta rota.

    Com a fonte simulada, `passo` permite pausar ou acelerar; com a fonte banco, `passo` e ignorado.
    """
    return _montar_status(fontes.fonte_ativa(), talhao, passo, simular_falha_llm)


@app.get("/simulador/leituras")
def simulador_leituras(passo: int | None = Query(None, ge=0), talhao: str | None = None,
                       simular_falha_llm: bool = False):
    """Sempre o simulador (dados SIMULADOS), mesmo quando a fonte ativa e o banco."""
    return _montar_status(SIMULADOR, talhao, passo, simular_falha_llm)


@app.post("/leituras", status_code=201)
async def receber_leitura(requisicao: Request):
    """Recebe uma leitura do gateway (token de dispositivo). Idempotente por (talhao, instante de coleta)."""
    try:
        ingestao.verificar_token(requisicao.headers.get("authorization"))
        try:
            corpo = await requisicao.json()
        except ValueError:
            raise ingestao.ErroIngestao(422, ["O corpo da requisição não é um JSON válido."])
        situacao, resposta = await run_in_threadpool(ingestao.registrar, corpo)
        return JSONResponse(status_code=situacao, content=resposta)
    except ingestao.ErroIngestao as erro:
        cabecalhos = {"WWW-Authenticate": "Bearer"} if erro.status == 401 else None
        return JSONResponse(status_code=erro.status, content={"erros": erro.erros}, headers=cabecalhos)


@app.get("/disponibilidade")
def obter_disponibilidade(horas: int = Query(72, ge=1, le=24 * 30)):
    """Indicador do relatorio: leituras validas recebidas / esperadas na janela (meta >= 95% em 72 h)."""
    return indicadores.disponibilidade(horas)


@app.get("/historico")
def historico(talhao: str = "A", horas: int = Query(24, ge=2, le=72)):
    """Uma leitura por hora da fonte ativa (simulada: hora simulada), classificada pelo modelo (sem LLM)."""
    if not _talhao_existe(talhao):
        return JSONResponse(status_code=404, content={"erros": [f"Talhão desconhecido: {talhao}."]})
    pontos = []
    for leitura in fontes.fonte_ativa().historico(talhao, horas):
        if leitura["umidade_solo"] is None:
            pontos.append(leitura | {"classe": None, "rotulo": "Sem dados"})
            continue
        classe, _, _ = classificador.classificar(leitura)
        pontos.append(leitura | {"classe": classe, "rotulo": classificador.ROTULOS[classe]})
    return pontos


# Paginas estaticas por ultimo, para nao esconder as rotas da API.
app.mount("/", StaticFiles(directory=RAIZ / "web", html=True), name="web")
