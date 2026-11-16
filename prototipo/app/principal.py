"""API do AgroAnalise (prototipo, dados SIMULADOS). Tambem serve as paginas de ../web.

Subir: uvicorn app.principal:app            (no deploy: --host 0.0.0.0 --port $PORT --proxy-headers)
"""
import asyncio
import contextlib
import json
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, FastAPI, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.exc import SQLAlchemyError

from app import (alimentador, banco, classificador, explicacao, faixas, fontes, indicadores, ingestao, riscos, seguranca,
                 servico)
from app.banco import BancoIndisponivel
from app.validacao import ErroValidacao

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
registro = logging.getLogger("agroanalise.api")

CENARIOS = [
    {"id": "ideal", "nome": "Ideal", "especie": "Arabica", "umidade_solo": 55, "temperatura": 21, "umidade_ar": 72},
    {"id": "solo_seco", "nome": "Solo seco", "especie": "Arabica", "umidade_solo": 33, "temperatura": 22, "umidade_ar": 70},
    {"id": "calor_excessivo", "nome": "Calor excessivo", "especie": "Conilon", "umidade_solo": 50, "temperatura": 38, "umidade_ar": 65},
    {"id": "muito_seco", "nome": "Solo muito seco", "especie": "Conilon", "umidade_solo": 12, "temperatura": 31, "umidade_ar": 50},
    {"id": "sem_dados", "nome": "Sem dados", "especie": "Arabica", "umidade_solo": None, "temperatura": None, "umidade_ar": None},
]
SIMULADOR = fontes.FonteSimulada()
rotas = APIRouter()


def _falha_llm_pedida(simular_falha_llm):
    """?simular_falha_llm=true so vale no modo demonstracao. Devolve (forcar_falha, resposta_de_erro)."""
    if simular_falha_llm and not seguranca.modo_demo():
        return False, seguranca.erro_so_no_modo_demo()
    return simular_falha_llm, None


@rotas.get("/saude")
def saude():
    return {"estado": "ok", "modelo_carregado": classificador.modelo_disponivel(),
            "llm_configurado": explicacao.llm_configurado(), "llm_uso": explicacao.uso_do_llm(),
            "modo_demonstracao": True, "modo_demo": seguranca.modo_demo(),
            "fonte_leituras": fontes.fonte_ativa().nome, "banco": banco.descrever_url(),
            "banco_disponivel": banco.verificar(),
            "recebimento_leituras_ligado": ingestao.token_configurado(), "alimentador_demo": alimentador.ligado()}


@rotas.post("/classificar")
async def classificar(requisicao: Request, simular_falha_llm: bool = False):
    forcar_falha, erro = _falha_llm_pedida(simular_falha_llm)
    if erro:
        return erro
    try:
        corpo = await requisicao.json()
    except ValueError:
        return JSONResponse(status_code=422, content={"erros": ["O corpo da requisição não é um JSON válido."]})
    try:
        # A chamada ao LLM e sincrona (httpx, ate 5 s): roda no pool de threads para nao travar o servidor.
        # Mantemos a rota async para ler o JSON manualmente e devolver erros em portugues simples.
        return await run_in_threadpool(servico.avaliar, corpo, forcar_falha)
    except ErroValidacao as erro_validacao:
        return JSONResponse(status_code=422, content={"erros": erro_validacao.erros})


@rotas.get("/faixas")
def obter_faixas():
    """Faixas provisorias, limites fisicos e intervalo de treino (a interface limita os controles por aqui)."""
    return faixas.carregar_faixas()


@rotas.get("/metricas")
def metricas():
    caminho = RAIZ / "ml" / "saida" / "metricas.json"
    if not caminho.exists():
        return JSONResponse(status_code=404,
                            content={"erros": ["Métricas não geradas. Rode: python ml/treinar.py --salvar"]})
    return json.loads(caminho.read_text(encoding="utf-8"))


@rotas.get("/cenarios")
def cenarios():
    return CENARIOS


def _talhao_existe(talhao):
    return any(t["id"] == talhao for t in fontes.fonte_ativa().talhoes())


@rotas.get("/talhoes")
def talhoes():
    fonte = fontes.fonte_ativa()
    return {"fonte": fonte.nome, "origem_dados": fonte.origem, "talhoes": fonte.talhoes()}


def _montar_status(fonte, talhao, passo, simular_falha_llm):
    forcar_falha, erro = _falha_llm_pedida(simular_falha_llm)
    if erro:
        return erro
    if talhao is not None and not _talhao_existe(talhao):
        return JSONResponse(status_code=404, content={"erros": [f"Talhão desconhecido: {talhao}."]})
    simulada = isinstance(fonte, fontes.FonteSimulada)
    passo = (fontes.passo_atual() if passo is None else passo) if simulada else None
    leituras = [l for l in fonte.leituras(passo) if talhao is None or l["talhao_id"] == talhao]
    nomes = {t["id"]: t for t in fonte.talhoes()}
    corpo = {"fonte": fonte.nome, "origem_dados": fonte.origem, "propriedade": fontes.PROPRIEDADE,
             "modo_demonstracao": True, "gerado_em": servico.agora(), "passo": passo,
             "leituras": [nomes[l["talhao_id"]] | servico.avaliar_leitura_de_fonte(l, forcar_falha)
                          for l in leituras]}
    if simulada:
        corpo |= {"passo_relogio": fontes.passo_atual(), "hora_simulada": fontes.hora_simulada(passo),
                  "segundos_por_passo": fontes.SEGUNDOS_POR_PASSO, "minutos_por_passo": fontes.MINUTOS_POR_PASSO}
    else:
        corpo |= {"minutos_desatualizado": fonte.minutos_desatualizado}
    return corpo


@rotas.get("/status")
def status(talhao: str | None = None, passo: int | None = Query(None, ge=0), simular_falha_llm: bool = False):
    """Estado atual de cada talhao, vindo da fonte ativa (FONTE_LEITURAS). As paginas usam esta rota.

    Com a fonte simulada, `passo` permite pausar ou acelerar; com a fonte banco, `passo` e ignorado.
    """
    return _montar_status(fontes.fonte_ativa(), talhao, passo, simular_falha_llm)


@rotas.get("/simulador/leituras")
def simulador_leituras(passo: int | None = Query(None, ge=0), talhao: str | None = None,
                       simular_falha_llm: bool = False):
    """Sempre o simulador (dados SIMULADOS), mesmo quando a fonte ativa e o banco. So no modo demonstracao."""
    if not seguranca.modo_demo():
        return seguranca.erro_so_no_modo_demo()
    return _montar_status(SIMULADOR, talhao, passo, simular_falha_llm)


@rotas.post("/leituras", status_code=201)
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


@rotas.get("/disponibilidade")
def obter_disponibilidade(horas: int = Query(72, ge=1, le=24 * 30)):
    """Indicador do relatorio: leituras validas recebidas / esperadas na janela (meta >= 95% em 72 h)."""
    return indicadores.disponibilidade(horas)


@rotas.get("/historico")
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


@rotas.get("/riscos/regioes")
def riscos_regioes():
    """Regioes de demonstracao do mapa (centros aproximados). O navegador escolhe a mais proxima localmente."""
    return {"regioes": riscos.provedor_ativo().regioes(), "origem_dados": "simulado"}


@rotas.get("/riscos/{regiao_id}")
def riscos_da_regiao(regiao_id: str):
    """Camadas de risco SIMULADAS de uma regiao (GeoJSON), por regiao_id: nunca por coordenada do usuario."""
    if regiao_id not in riscos.REGIOES:
        return JSONResponse(status_code=404, content={"erros": [f"Região desconhecida: {regiao_id}."]})
    provedor = riscos.provedor_ativo()
    orientacoes = riscos.carregar_orientacoes()
    return {"regiao": riscos.REGIOES[regiao_id], "origem_dados": provedor.origem, "provedor": provedor.nome,
            "aviso": orientacoes["aviso"], "emergencia": orientacoes["emergencia"],
            "orientacoes_revisadas_por_humano": orientacoes["revisado_por_humano"],
            "tipos": {t: info | {"o_que_fazer": orientacoes["tipos"][t]["o_que_fazer"],
                                 "fonte_oficial": orientacoes["tipos"][t]["fonte_oficial"]}
                      for t, info in riscos.TIPOS.items()},
            "camadas": provedor.camadas(regiao_id)}


def _fonte_configurada_e_banco():
    return (os.getenv("FONTE_LEITURAS") or "simulada").strip().lower() == "banco"


@asynccontextmanager
async def ciclo_de_vida(_app):
    banco_ok = False
    try:
        banco.configurar()  # cria as tabelas se ainda nao existirem (migracao simples)
        banco_ok = True
    except Exception as erro:  # fail-soft: a demonstracao simulada nao depende do banco
        registro.warning("Banco indisponível no startup (%s); seguindo com a fonte configurada.",
                         type(erro).__name__)
        if _fonte_configurada_e_banco():
            raise
    if banco_ok and os.getenv("SEMEAR_SE_VAZIO", "").strip().lower() in ("1", "true", "sim"):
        try:
            if banco.contar_leituras() == 0:
                from app.semear import semear
                registro.info("Banco vazio: semente de leituras simuladas: %s", await run_in_threadpool(semear, 72))
        except Exception as erro:
            registro.warning("Falha ao consultar/semear o banco (%s).", type(erro).__name__)
            if _fonte_configurada_e_banco():
                raise
    tarefa = asyncio.create_task(alimentador.laco()) if alimentador.ligado() else None
    try:
        yield
    finally:
        if tarefa:
            tarefa.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await tarefa
        banco.fechar()


def criar_app():
    """Monta o app. As protecoes dependem de variaveis de ambiente lidas aqui (CORS) ou a cada pedido (o resto)."""
    aplicacao = FastAPI(title="AgroAnálise (protótipo)", description="Dados simulados, modo demonstração.",
                        lifespan=ciclo_de_vida)
    aplicacao.state.limitador = seguranca.LimitadorDeTaxa()

    @aplicacao.middleware("http")
    async def protecoes(requisicao: Request, chamar_proximo):
        ip = requisicao.client.host if requisicao.client else "desconhecido"
        permitido, espera = requisicao.app.state.limitador.permitir(ip, requisicao.url.path, requisicao.method)
        if not permitido:
            resposta = JSONResponse(status_code=429, headers={"Retry-After": str(espera)}, content={"erros": [
                f"Muitos pedidos seguidos. Espere {espera} s e tente de novo."]})
        else:
            resposta = await chamar_proximo(requisicao)
        return seguranca.cabecalhos_de_seguranca(resposta, requisicao.url.scheme == "https")

    origens = seguranca.origens_permitidas()
    if origens:  # sem a variavel, so a propria origem (as paginas sao servidas pela API)
        aplicacao.add_middleware(CORSMiddleware, allow_origins=origens, allow_methods=["GET", "POST"],
                                 allow_headers=["Authorization", "Content-Type"])
    aplicacao.add_middleware(seguranca.LimiteDeCorpo)

    @aplicacao.exception_handler(BancoIndisponivel)
    @aplicacao.exception_handler(SQLAlchemyError)
    async def banco_indisponivel(requisicao: Request, erro: Exception):
        registro.warning("Banco indisponível em %s (%s).", requisicao.url.path, type(erro).__name__)
        return JSONResponse(status_code=503, headers={"Retry-After": "5"}, content={
            "erros": ["Banco de dados indisponível no momento. Tente novamente em instantes."]})

    aplicacao.include_router(rotas)
    # Paginas estaticas por ultimo, para nao esconder as rotas da API.
    aplicacao.mount("/", StaticFiles(directory=RAIZ / "web", html=True), name="web")
    return aplicacao


app = criar_app()
