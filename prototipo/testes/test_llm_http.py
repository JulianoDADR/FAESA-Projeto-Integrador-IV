"""Integracao com o provedor do LLM pelo caminho HTTP real (_chamar_llm), com o httpx simulado. Nunca usa a rede."""
import logging

import httpx
import pytest

from app import explicacao

CHAVE = "gsk_chave_de_teste_que_nao_pode_vazar"
LEITURA = {"especie": "Conilon", "umidade_solo": 15.0, "temperatura": 26.0, "umidade_ar": 72.0}


@pytest.fixture
def com_chave(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", CHAVE)
    monkeypatch.setenv("GROQ_MODELO", "modelo-de-teste")


def _resposta(conteudo, uso=None, status=200):
    corpo = {"choices": [{"message": {"content": conteudo}}], "usage": uso or {"prompt_tokens": 150, "completion_tokens": 20}}
    return httpx.Response(status, json=corpo, request=httpx.Request("POST", explicacao.URL_GROQ))


def test_pedido_ao_groq_tem_modelo_limites_e_token_no_cabecalho(com_chave, monkeypatch):
    pedidos = []

    def post_falso(url, json, headers, timeout):
        pedidos.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return _resposta("Há leitura bem fora do ideal. Vá até a lavoura e avalie a situação.")
    monkeypatch.setattr(explicacao.httpx, "post", post_falso)
    mensagem, origem = explicacao.gerar_mensagem("Vermelho", LEITURA)
    assert origem == "llm" and mensagem.startswith("Há leitura")
    p = pedidos[0]
    assert p["url"] == explicacao.URL_GROQ and p["headers"]["Authorization"] == f"Bearer {CHAVE}"
    assert p["json"]["model"] == "modelo-de-teste" and p["json"]["max_tokens"] <= 150 and p["timeout"] <= 5
    # so dados estruturados no pedido: a instrucao fixa do sistema e a linha com classe, especie e numeros
    assert [m["role"] for m in p["json"]["messages"]] == ["system", "user"]
    assert p["json"]["messages"][1]["content"].startswith("Classe: Vermelho. Espécie: Conilon.")
    uso = explicacao.uso_do_llm()
    assert uso["chamadas"] == 1 and uso["tokens_entrada"] == 150 and uso["tokens_saida"] == 20


@pytest.mark.parametrize("efeito, descricao", [
    (httpx.ReadTimeout("tempo esgotado"), "timeout"),
    (httpx.ConnectError("sem rede"), "sem conexão"),
    (httpx.Response(429, json={"error": {"message": "rate limit"}}), "429 do plano gratuito"),
    (httpx.Response(401, json={"error": "invalid api key"}), "chave inválida"),
    (httpx.Response(503, text="indisponível"), "503"),
    (httpx.Response(200, text="isto não é json"), "JSON malformado"),
    (httpx.Response(200, json={"choices": []}), "sem escolhas"),
])
def test_falhas_do_provedor_viram_mensagem_padrao(com_chave, monkeypatch, efeito, descricao):
    def post_falso(*_, **__):
        if isinstance(efeito, Exception):
            raise efeito
        efeito.request = httpx.Request("POST", explicacao.URL_GROQ)
        return efeito
    monkeypatch.setattr(explicacao.httpx, "post", post_falso)
    mensagem, origem = explicacao.gerar_mensagem("Vermelho", LEITURA)
    assert origem == "padrao", descricao
    assert mensagem == explicacao.MENSAGENS_PADRAO["Vermelho"]
    assert explicacao.uso_do_llm()["falhas"] == 1


@pytest.mark.parametrize("texto", ["Fique tranquilo, está tudo certo.", "Aplique 30 litros de água por planta agora.",
                                   "Everything is fine.", "Uma frase. Outra frase. Mais uma. E mais outra."])
def test_saida_ruim_pelo_http_vira_mensagem_padrao_e_e_contada(com_chave, monkeypatch, texto):
    monkeypatch.setattr(explicacao.httpx, "post", lambda *_, **__: _resposta(texto))
    assert explicacao.gerar_mensagem("Vermelho", LEITURA)[1] == "padrao"
    assert explicacao.uso_do_llm()["rejeitadas"] == 1


def test_chave_nunca_aparece_nos_logs(com_chave, monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(explicacao.httpx, "post", lambda *_, **__: _resposta("Há leitura bem fora do ideal. Vá até a lavoura."))
    explicacao.gerar_mensagem("Vermelho", LEITURA)
    explicacao.limpar_cache()
    monkeypatch.setattr(explicacao.httpx, "post", lambda *_, **__: (_ for _ in ()).throw(httpx.ConnectError("x")))
    explicacao.gerar_mensagem("Vermelho", LEITURA | {"umidade_solo": 5.0})
    assert caplog.records and CHAVE not in caplog.text


def test_cache_evita_segunda_chamada_na_mesma_faixa(com_chave, monkeypatch):
    chamadas = []
    monkeypatch.setattr(explicacao.httpx, "post",
                        lambda *_, **__: chamadas.append(1) or _resposta("Há leitura bem fora do ideal. Vá até a lavoura."))
    explicacao.gerar_mensagem("Vermelho", LEITURA)
    explicacao.gerar_mensagem("Vermelho", LEITURA | {"umidade_solo": 15.4})  # mesma faixa de valores
    assert len(chamadas) == 1
