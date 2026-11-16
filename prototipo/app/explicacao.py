"""Camada de explicacao: o LLM (GroqCloud) so REFORMULA a classe calculada pelo classificador.

Regras do relatorio (secao 6.4): entrada somente estruturada, no maximo 2 frases, sem recomendacao
agronomica especifica, validacao da saida, mensagens-padrao de contingencia e cache.
A chamada a API fica isolada em `_chamar_llm`, para poder trocar de provedor.
"""
import logging
import os
import re
import time
from collections import deque
from datetime import datetime, timezone
from threading import Lock

import httpx

registro = logging.getLogger("agroanalise.explicacao")

URL_GROQ = "https://api.groq.com/openai/v1/chat/completions"
MODELO_PADRAO = "openai/gpt-oss-20b"
TEMPO_LIMITE_S = 5.0
MAX_CARACTERES = 280
MAX_TOKENS_GPT_OSS = 512  # inclui os tokens de raciocinio; a saida final continua limitada por MAX_CARACTERES

MENSAGENS_PADRAO = {
    "Verde": "As leituras estão dentro do esperado agora. Siga acompanhando a lavoura e as próximas leituras.",
    "Amarelo": "Alguma leitura está saindo do ideal. Vale olhar a lavoura e conferir a próxima leitura.",
    "Vermelho": "Há leitura bem fora do ideal. Vá até a lavoura e avalie a situação; a decisão de manejo é sua.",
}

INSTRUCAO_SISTEMA = (
    "Você escreve avisos curtos para agricultores familiares de café, em português do Brasil, com palavras simples. "
    "A classe do semáforo JÁ foi decidida por outro sistema; você NÃO decide nem muda a classe, só a explica. "
    "Escreva no máximo 2 frases. Não recomende produtos, doses, adubos, defensivos nem volumes de irrigação. "
    "Lembre, de forma breve, que a decisão de manejo é do produtor. "
    "Verde: tom calmo. Amarelo: pedir para observar e acompanhar. Vermelho: pedir para ir até a lavoura e avaliar. "
    "Não use números nem emojis. Responda só com o aviso."
)

_cache = {}

# Teto de chamadas ao Groq (protege a cota do plano gratuito; conferir os limites vigentes do plano no console).
# Ao estourar, a mensagem-padrao e usada: o semaforo nunca depende do LLM.
TETO_POR_MINUTO_PADRAO = 20
TETO_POR_DIA_PADRAO = 1000
_trava = Lock()
_chamadas_ultimo_minuto = deque()
_uso = {"dia": None, "chamadas": 0, "tokens_entrada": 0, "tokens_saida": 0, "falhas": 0, "rejeitadas": 0,
        "teto_atingido": 0}


def _teto(nome, padrao):
    try:
        return int(os.getenv(nome, padrao))
    except ValueError:
        return padrao


def _virar_dia():
    hoje = datetime.now(timezone.utc).date().isoformat()
    if _uso["dia"] != hoje:
        _uso.update({"dia": hoje, "chamadas": 0, "tokens_entrada": 0, "tokens_saida": 0, "falhas": 0,
                     "rejeitadas": 0, "teto_atingido": 0})


def reservar_chamada(relogio=time.monotonic):
    """Conta uma chamada se couber nos tetos. Devolve False quando o teto do minuto ou do dia foi atingido."""
    with _trava:
        _virar_dia()
        agora = relogio()
        while _chamadas_ultimo_minuto and agora - _chamadas_ultimo_minuto[0] >= 60:
            _chamadas_ultimo_minuto.popleft()
        if (len(_chamadas_ultimo_minuto) >= _teto("GROQ_MAX_POR_MINUTO", TETO_POR_MINUTO_PADRAO)
                or _uso["chamadas"] >= _teto("GROQ_MAX_POR_DIA", TETO_POR_DIA_PADRAO)):
            _uso["teto_atingido"] += 1
            return False
        _chamadas_ultimo_minuto.append(agora)
        _uso["chamadas"] += 1
        return True


def _anotar(chave, quantidade=1):
    with _trava:
        _virar_dia()
        _uso[chave] += quantidade or 0


def uso_do_llm():
    """Uso do dia (UTC): chamadas, tokens, falhas, saidas rejeitadas e vezes em que o teto segurou. Sem segredos."""
    with _trava:
        _virar_dia()
        return dict(_uso) | {"teto_por_minuto": _teto("GROQ_MAX_POR_MINUTO", TETO_POR_MINUTO_PADRAO),
                             "teto_por_dia": _teto("GROQ_MAX_POR_DIA", TETO_POR_DIA_PADRAO)}


def zerar_uso():
    with _trava:
        _chamadas_ultimo_minuto.clear()
        _uso["dia"] = None
        _virar_dia()


def _faixa(valor, passo):
    return int(valor // passo)


def chave_cache(classe, leitura):
    return (classe, leitura["especie"], _faixa(leitura["umidade_solo"], 10),
            _faixa(leitura["temperatura"], 2), _faixa(leitura["umidade_ar"], 10))


def limpar_cache():
    _cache.clear()


def llm_configurado():
    return bool(os.getenv("GROQ_API_KEY"))


def montar_mensagens(classe, leitura):
    """Monta o pedido ao LLM SOMENTE com campos estruturados e ja validados.

    O Groq recomenda, para o GPT-OSS, concentrar as instrucoes na mensagem do usuario em vez de usar `system`.
    O texto continua fixo no servidor e nenhum campo livre do usuario entra no pedido.
    """
    dados = (f"Classe: {classe}. Espécie: {leitura['especie']}. "
             f"Umidade do solo: {leitura['umidade_solo']:.0f}%. "
             f"Temperatura: {leitura['temperatura']:.0f} graus. "
             f"Umidade do ar: {leitura['umidade_ar']:.0f}%.")
    return [{"role": "user", "content": f"{INSTRUCAO_SISTEMA}\n\nDados da leitura:\n{dados}"}]


def _chamar_llm(mensagens):
    """Unico ponto de contato com o provedor (Groq, API compativel com OpenAI)."""
    chave = os.getenv("GROQ_API_KEY")
    if not chave:
        raise RuntimeError("GROQ_API_KEY não configurada")
    modelo = os.getenv("GROQ_MODELO", MODELO_PADRAO)
    corpo = {"model": modelo, "messages": mensagens, "temperature": 0.3}
    if modelo.startswith("openai/gpt-oss"):
        corpo |= {"max_completion_tokens": MAX_TOKENS_GPT_OSS, "reasoning_effort": "low", "include_reasoning": False}
    else:  # compatibilidade com modelos anteriores, que usam max_tokens
        corpo["max_tokens"] = 120
    inicio = time.monotonic()
    resposta = httpx.post(URL_GROQ, json=corpo, headers={"Authorization": f"Bearer {chave}"},
                          timeout=TEMPO_LIMITE_S)
    resposta.raise_for_status()
    dados = resposta.json()
    uso = dados.get("usage", {})
    _anotar("tokens_entrada", uso.get("prompt_tokens"))
    _anotar("tokens_saida", uso.get("completion_tokens"))
    registro.info("chamada LLM ok: %.2fs, tokens entrada=%s saida=%s", time.monotonic() - inicio,
                  uso.get("prompt_tokens"), uso.get("completion_tokens"))
    return dados["choices"][0]["message"]["content"]


# ---------- validacao da saida do LLM ----------
_DOSE_VOLUME = re.compile(r"\d+[.,]?\d*\s*(mg|g|kg|ml|l|litros?|m3|m³|mm|gramas?|quilos?|doses?)\b", re.I)
_PRODUTOS = re.compile(r"\b(dose|doses|litros?|adubo|adubar|fertiliz\w*|fungicida|herbicida|inseticida|calda|defensivo)\b", re.I)
# Ordens de manejo (mesmo sem numeros): o sistema nao recomenda manejo, so pede para olhar a lavoura.
# Acrescentado depois da avaliacao de 2026-11-15 (docs/avaliacao/llm.md), em que "Regue bastante a lavoura" passou.
_MANEJO = re.compile(r"\b(regue|reguem|regar|irrigue|irriguem|irrigar|aplique|apliquem|aplicar|adube|pulverize|pulverizar|molhe|molhar)\b", re.I)
_PROIBIDO_VERDE = re.compile(
    r"cr[ií]tic|urgen|grave|perig|risco|preocup|aten[cç][aã]o"
    # Falso alarme (relatorio, Quadro 3: Verde = tom calmo). Simetrico a regra do Vermelho: Verde nao manda ir a
    # lavoura com pressa nem sugere dano a planta. Acrescentado em 2026-11-16 pelo principio, nao pelas palavras do
    # banco de avaliacao; testado com frases novas em testes/test_explicacao.py.
    r"|\b(v[aá]|corra|corram)\s+(at[eé]|l[aá]|ver|conferir|olhar|checar|verificar)\b"
    r"|\b(logo|imediatamente|depressa|rapidamente|quanto antes|sem demora|alerta|esperto)\b"
    r"|\b(sofr\w*|estress\w*|murch\w*|dan[oi]\w*|prejud\w*|preju[ií]z\w*)\b", re.I)
_PROIBIDO_AMARELO = re.compile(r"cr[ií]tic|urgen|grave|perig|tudo (bem|certo)|tranquil|[oó]tim", re.I)
_PROIBIDO_VERMELHO = re.compile(r"tudo (bem|certo)|tranquil|[oó]tim|sem problema|dentro do (ideal|esperado)|condi[cç][oõ]es (ideais|boas)", re.I)
_PROIBIDO = {"Verde": _PROIBIDO_VERDE, "Amarelo": _PROIBIDO_AMARELO, "Vermelho": _PROIBIDO_VERMELHO}
_PEDE_VERIFICACAO = re.compile(r"\b(vá|vai|ir|confira|conferir|verifique|verificar|avalie|avaliar|olhe|olhar|veja|ver)\b", re.I)
# Deteccao simples de idioma: palavras comuns do portugues contra marcas de ingles e espanhol.
# Ampliada depois da avaliacao de 2026-11-15: a lista curta antiga recusava frases curtas em portugues
# (ex.: "Fique tranquilo, está tudo certo.") como "não parece português".
_PALAVRAS_PT = {"o", "a", "os", "as", "de", "do", "da", "dos", "das", "e", "em", "na", "no", "nas", "nos", "ao",
                "para", "pela", "pelo", "por", "com", "que", "é", "um", "uma", "se", "não", "mas", "ou", "só", "há",
                "está", "estão", "tudo", "mais", "muito", "bem", "hoje", "agora", "até", "sua", "seu", "pode", "vá",
                "fique", "siga", "olhe", "ver", "lavoura", "solo", "café", "leitura", "leituras", "ar"}
_PALAVRAS_ESTRANGEIRAS = {"the", "is", "and", "your", "with", "today", "field", "looks", "fine", "everything",
                          "el", "en", "del", "hoy", "situación", "revise", "cafetal", "bien", "muy"}


def motivos_de_rejeicao(texto, classe):
    """Todos os problemas encontrados na saida, na ordem de prioridade. Lista vazia = mensagem aceita."""
    if not isinstance(texto, str) or not texto.strip():
        return ["vazia"]
    texto = texto.strip()
    motivos = []
    if len(texto) > MAX_CARACTERES:
        motivos.append("longa demais")
    if len(re.findall(r"[.!?](\s|$)", texto)) > 2:
        motivos.append("mais de 2 frases")
    palavras = set(re.findall(r"[\wáéíóúâêôãõçñ]+", texto.lower()))
    portugues, estrangeiras = len(palavras & _PALAVRAS_PT), len(palavras & _PALAVRAS_ESTRANGEIRAS)
    if re.search(r"[Ѐ-ӿ぀-ヿ一-鿿ñ¿¡]", texto) or estrangeiras > portugues or portugues == 0:
        motivos.append("não parece português")
    if _DOSE_VOLUME.search(texto) or _PRODUTOS.search(texto) or _MANEJO.search(texto):
        motivos.append("dose, volume ou produto")
    # Vermelho precisa pedir a verificacao da area (relatorio, Quadro 3): uma mensagem que so acalma e o pior erro.
    if _PROIBIDO[classe].search(texto) or (classe == "Vermelho" and not _PEDE_VERIFICACAO.search(texto)):
        motivos.append("incoerente com a classe")
    return motivos


def validar_saida(texto, classe):
    """Devolve (ok, motivo). So aceita mensagem curta, em portugues, coerente e sem dose/volume."""
    motivos = motivos_de_rejeicao(texto, classe)
    return (not motivos), (motivos[0] if motivos else "")


def gerar_mensagem(classe, leitura, forcar_falha=False):
    """Devolve (mensagem, origem) com origem 'llm' ou 'padrao'. Nunca levanta erro por causa do LLM."""
    padrao = (MENSAGENS_PADRAO[classe], "padrao")
    if forcar_falha:
        registro.info("falha do LLM simulada a pedido")
        return padrao
    if not llm_configurado():
        return padrao
    chave = chave_cache(classe, leitura)
    if chave in _cache:
        return _cache[chave], "llm"
    if not reservar_chamada():
        registro.warning("Teto de chamadas ao LLM atingido; usando mensagem-padrão.")
        return padrao
    try:
        texto = _chamar_llm(montar_mensagens(classe, leitura))
    except Exception as erro:  # rede, limite do plano, timeout, chave invalida: o semaforo segue sem o LLM
        _anotar("falhas")
        registro.warning("LLM indisponível, usando mensagem-padrão: %s", type(erro).__name__)
        return padrao
    ok, motivo = validar_saida(texto, classe)
    if not ok:
        _anotar("rejeitadas")
        registro.warning("saída do LLM rejeitada (%s), usando mensagem-padrão", motivo)
        return padrao
    _cache[chave] = texto.strip()
    return _cache[chave], "llm"
