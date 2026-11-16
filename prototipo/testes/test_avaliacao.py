"""Etapa 6: filtro de saida depois da avaliacao e scripts de avaliacao (sem gravar os relatorios)."""
import sys
from pathlib import Path
from unittest import mock

import pytest

from app import explicacao

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ml"))


# ---------- filtro ajustado na avaliacao de 2026-11-15 ----------
@pytest.mark.parametrize("texto", ["Regue bastante a lavoura hoje.", "Vale irrigar a lavoura agora.",
                                   "Aplique adubo no talhão.", "Pulverize as plantas amanhã cedo."])
def test_ordens_de_manejo_sao_bloqueadas_mesmo_sem_numeros(texto):
    ok, motivo = explicacao.validar_saida(texto, "Amarelo")
    assert not ok and motivo == "dose, volume ou produto"


@pytest.mark.parametrize("texto, classe", [
    ("Fique tranquilo, está tudo certo.", "Vermelho"),   # curta, em portugues: antes era recusada como idioma
    ("Está tudo ótimo, pode ficar tranquilo.", "Amarelo"),
])
def test_frase_curta_em_portugues_chega_na_checagem_de_coerencia(texto, classe):
    motivos = explicacao.motivos_de_rejeicao(texto, classe)
    assert "não parece português" not in motivos and "incoerente com a classe" in motivos


@pytest.mark.parametrize("texto", ["Everything looks fine with your coffee field today.",
                                   "Situación crítica en el cafetal, revise hoy."])
def test_ingles_e_espanhol_sao_recusados(texto):
    assert "não parece português" in explicacao.motivos_de_rejeicao(texto, "Verde")


def test_vermelho_sem_pedido_de_verificacao_e_recusado():
    assert not explicacao.validar_saida("Nada de muito sério, só acompanhe com calma.", "Vermelho")[0]
    assert explicacao.validar_saida("O solo está muito seco. Vá até a lavoura e avalie hoje.", "Vermelho")[0]


def test_frases_boas_tipicas_continuam_aceitas():
    for classe, texto in [("Verde", "O solo e o clima estão bons para o café agora. Siga acompanhando."),
                          ("Amarelo", "Alguma leitura está saindo do ideal. Vale observar a lavoura."),
                          ("Vermelho", "Há leitura bem fora do ideal. Vá até a lavoura e avalie a situação.")]:
        assert explicacao.validar_saida(texto, classe) == (True, "")


# ---------- avaliacao do LLM (modo mock) ----------
def test_avaliacao_mock_nunca_leva_caso_de_borda_ao_llm_e_nunca_quebra():
    import avaliar_llm
    with mock.patch.dict("os.environ", {"GROQ_API_KEY": "chave-falsa", "GROQ_MAX_POR_MINUTO": "100000"}):
        resultados = avaliar_llm.rodar_cenarios(ao_vivo=False)
        resumo = avaliar_llm.resumir(resultados, ao_vivo=False)
    assert resumo["cenarios"] == 30 and resumo["validos"] == 24 and resumo["borda"] == 6
    assert resumo["borda_recusados_422"] == 6 and resumo["borda_chamou_llm"] == 0
    assert resumo["validos_chamaram_llm"] == 24 and resumo["validos_sem_chamada_por_teto"] == 0
    # 7 do LLM depois da regra de falso alarme no Verde (2026-11-16); antes eram 8, com 1 inadequada exibida
    assert resumo["mensagem_do_llm_exibida"] == 7 and resumo["mensagem_padrao_exibida"] == 17
    assert resumo["inadequadas_exibidas_ao_usuario"] == 0
    assert resumo["exibidas_com_mais_de_2_frases"] == 0
    # nenhuma resposta inadequada do banco chega ao usuario numa classe Vermelho (o pior erro)
    vermelhos_ruins = [r for r in resultados if r["tipo"] == "valido" and r["classe"] == "Vermelho"
                       and r["origem_mensagem"] == "llm" and not r["resposta_llm"]["adequada"]]
    assert vermelhos_ruins == []


def test_falhas_da_api_pelo_caminho_http_caem_na_mensagem_padrao():
    import avaliar_llm
    casos = {c["caso"]: c for c in avaliar_llm.falhas_da_api()}
    for nome in ("tempo esgotado", "HTTP 429 (limite do plano)", "HTTP 500", "JSON sem 'choices'"):
        assert casos[nome]["origem_mensagem"] == "padrao" and casos[nome]["falhas"] == 1
    assert casos["resposta OK"]["origem_mensagem"] == "llm" and casos["resposta OK"]["tokens_entrada"] == 180


# ---------- avaliacao do classificador ----------
def test_intervalo_de_wilson():
    from avaliar_classificador import wilson
    baixo, alto = wilson(237, 257)
    assert baixo < 237 / 257 < alto and 0.88 < baixo < 0.89 and 0.94 < alto < 0.95
    assert wilson(0, 0) == [0.0, 0.0]
