"""Uma chamada lenta ao LLM nao pode travar o servidor para os outros pedidos."""
import asyncio
import time

import httpx

from app import explicacao
from app.principal import app

ESPERA_LLM_S = 0.8


def test_llm_lento_nao_bloqueia_outras_rotas(monkeypatch, leitura_valida):
    monkeypatch.setenv("GROQ_API_KEY", "chave-de-teste")

    def llm_lento(_):
        time.sleep(ESPERA_LLM_S)  # simula a rede lenta com uma chamada sincrona, como a real
        return "As leituras estão dentro do esperado agora. Siga acompanhando a lavoura."
    monkeypatch.setattr(explicacao, "_chamar_llm", llm_lento)

    async def cenario():
        transporte = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transporte, base_url="http://teste") as cliente:
            inicio = time.monotonic()
            classificar = asyncio.create_task(cliente.post("/classificar", json=leitura_valida))
            await asyncio.sleep(0.05)  # garante que o /classificar ja esta esperando o LLM
            saude = await cliente.get("/saude")
            tempo_saude = time.monotonic() - inicio
            resposta = await classificar
            return saude, tempo_saude, resposta

    saude, tempo_saude, resposta = asyncio.run(cenario())
    assert saude.status_code == 200
    assert tempo_saude < ESPERA_LLM_S / 2, f"/saude esperou o LLM ({tempo_saude:.2f}s)"
    assert resposta.status_code == 200 and resposta.json()["origem_mensagem"] == "llm"
