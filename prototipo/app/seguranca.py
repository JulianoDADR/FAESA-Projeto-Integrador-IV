"""Protecoes da API publica: modo demonstracao, limite de requisicoes, tamanho maximo do corpo e cabecalhos.

- MODO_DEMO (1/true/sim): libera ?simular_falha_llm=true e /simulador/leituras. Desligado por padrao.
- Limite de requisicoes por IP (janela deslizante de 60 s, em memoria): protege a cota gratuita do Groq e o banco.
  Em memoria basta para uma unica instancia (plano gratuito); com varias instancias, cada uma conta a sua parte.
  O IP vem de request.client, que o uvicorn preenche com X-Forwarded-For quando roda com --proxy-headers.
- Corpo maximo de TAMANHO_MAXIMO_CORPO bytes (a maior leitura legitima tem menos de 300 bytes).
- Cabecalhos de seguranca basicos e CSP limitando scripts e estilos as origens que as paginas usam.
"""
import os
import time
from collections import defaultdict, deque
from threading import Lock

from fastapi.responses import JSONResponse

TAMANHO_MAXIMO_CORPO = 16 * 1024

# (prefixo da rota, metodo) -> pedidos por minuto por IP
LIMITES_POR_MINUTO = {
    ("/classificar", "POST"): 30,   # cada pedido pode chamar o LLM
    ("/leituras", "POST"): 300,     # gateway esvaziando a fila depois de uma queda
    ("/status", "GET"): 240,        # paginas consultam a cada 3 s (ou 0,75 s no 4x)
    ("/simulador", "GET"): 240,
    ("/historico", "GET"): 60,
    ("/disponibilidade", "GET"): 30,
    ("/riscos", "GET"): 60,
}

POLITICA_CONTEUDO = "; ".join([
    "default-src 'self'",
    # Tailwind (CDN de jogo) e os scripts das paginas sao inline; por isso 'unsafe-inline' e a lista de origens.
    "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com",
    "style-src 'self' 'unsafe-inline' https://unpkg.com",
    "img-src 'self' data: https://*.tile.openstreetmap.org https://tile.openstreetmap.org https://unpkg.com",
    "connect-src 'self'",
    "font-src 'self' data:",
    "frame-ancestors 'none'",
    "base-uri 'self'",
    "form-action 'self'",
])


def modo_demo():
    return os.getenv("MODO_DEMO", "").strip().lower() in ("1", "true", "sim", "yes")


def origens_permitidas():
    return [o.strip() for o in os.getenv("ORIGENS_PERMITIDAS", "").split(",") if o.strip()]


def erro_so_no_modo_demo():
    return JSONResponse(status_code=403, content={"erros": [
        "Recurso de demonstração desligado neste servidor (defina MODO_DEMO=1 para ligar)."]})


class LimitadorDeTaxa:
    def __init__(self, limites=None, janela_s=60.0, relogio=time.monotonic):
        self.limites = limites or LIMITES_POR_MINUTO
        self.janela_s = janela_s
        self.relogio = relogio
        self._pedidos = defaultdict(deque)
        self._trava = Lock()

    def limite_da_rota(self, caminho, metodo):
        for (prefixo, metodo_limite), limite in self.limites.items():
            if metodo == metodo_limite and (caminho == prefixo or caminho.startswith(prefixo + "/")):
                return prefixo, limite
        return None, None

    def permitir(self, ip, caminho, metodo):
        """Devolve (permitido, segundos_para_tentar_de_novo)."""
        prefixo, limite = self.limite_da_rota(caminho, metodo)
        if limite is None:
            return True, 0
        agora = self.relogio()
        with self._trava:
            fila = self._pedidos[(ip, prefixo, metodo)]
            while fila and agora - fila[0] >= self.janela_s:
                fila.popleft()
            if len(fila) >= limite:
                return False, max(1, int(self.janela_s - (agora - fila[0])) + 1)
            fila.append(agora)
            return True, 0


def cabecalhos_de_seguranca(resposta, https):
    resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
    resposta.headers.setdefault("X-Frame-Options", "DENY")
    resposta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    # Geolocalizacao so para a propria pagina (mapa de riscos, Etapa 3); camera e microfone nunca.
    resposta.headers.setdefault("Permissions-Policy", "geolocation=(self), camera=(), microphone=(), payment=()")
    resposta.headers.setdefault("Content-Security-Policy", POLITICA_CONTEUDO)
    if https:
        resposta.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
    return resposta


class LimiteDeCorpo:
    """Middleware ASGI: recusa corpos maiores que o limite (pelo Content-Length ou contando os bytes recebidos)."""

    def __init__(self, app, maximo=TAMANHO_MAXIMO_CORPO):
        self.app, self.maximo = app, maximo

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] not in ("POST", "PUT", "PATCH"):
            return await self.app(scope, receive, send)
        tamanho = dict(scope.get("headers") or []).get(b"content-length")
        if tamanho is not None and tamanho.isdigit() and int(tamanho) > self.maximo:
            return await self._recusar(scope, receive, send)
        recebidos = 0

        async def receber_contando():
            nonlocal recebidos
            mensagem = await receive()
            if mensagem["type"] == "http.request":
                recebidos += len(mensagem.get("body", b""))
                if recebidos > self.maximo:
                    raise CorpoGrandeDemais()
            return mensagem

        try:
            await self.app(scope, receber_contando, send)
        except* CorpoGrandeDemais:  # except*: o middleware http do Starlette pode embrulhar o erro num ExceptionGroup
            await self._recusar(scope, receive, send)

    async def _recusar(self, scope, receive, send):
        resposta = JSONResponse(status_code=413, content={"erros": [
            f"Pedido grande demais (máximo de {self.maximo // 1024} KB)."]})
        await resposta(scope, receive, send)


class CorpoGrandeDemais(Exception):
    pass
