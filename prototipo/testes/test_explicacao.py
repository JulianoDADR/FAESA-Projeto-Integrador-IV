import pytest

from app import explicacao

LEITURA = {"especie": "Arabica", "umidade_solo": 20.0, "temperatura": 22.0, "umidade_ar": 70.0}


def test_entrada_do_llm_so_tem_campos_estruturados():
    mensagens = explicacao.montar_mensagens("Vermelho", LEITURA)
    usuario = mensagens[1]["content"]
    assert "Classe: Vermelho" in usuario and "Arabica" in usuario and "20%" in usuario
    assert len(mensagens) == 2 and mensagens[0]["role"] == "system"


def test_sem_chave_usa_mensagem_padrao():
    mensagem, origem = explicacao.gerar_mensagem("Amarelo", LEITURA)
    assert origem == "padrao" and mensagem == explicacao.MENSAGENS_PADRAO["Amarelo"]


def test_llm_com_falha_cai_no_padrao(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "chave-de-teste")

    def falha(_):
        raise TimeoutError("sem rede")
    monkeypatch.setattr(explicacao, "_chamar_llm", falha)
    assert explicacao.gerar_mensagem("Vermelho", LEITURA)[1] == "padrao"


@pytest.mark.parametrize("classe", ["Verde", "Amarelo", "Vermelho"])
def test_mensagens_padrao_passam_na_propria_validacao(classe):
    assert explicacao.validar_saida(explicacao.MENSAGENS_PADRAO[classe], classe)[0]


@pytest.mark.parametrize("classe,texto", [
    ("Vermelho", "Fique tranquilo, o solo está ótimo."),
    ("Verde", "Situação crítica, aja com urgência na lavoura."),
    ("Amarelo", "O solo está seco, aplique 20 litros de água hoje."),
    ("Amarelo", "Use 5 g de adubo por planta para o solo."),
    ("Verde", "The soil is fine today and the crop looks good."),
    ("Verde", "O solo está bom. A lavoura está bem. As leituras estão certas. Siga assim."),
])
def test_saida_ruim_e_rejeitada(classe, texto):
    assert not explicacao.validar_saida(texto, classe)[0]


def test_saida_incoerente_do_llm_cai_no_padrao(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "chave-de-teste")
    monkeypatch.setattr(explicacao, "_chamar_llm", lambda _: "Fique tranquilo, está tudo ótimo na lavoura.")
    mensagem, origem = explicacao.gerar_mensagem("Vermelho", LEITURA)
    assert origem == "padrao" and mensagem == explicacao.MENSAGENS_PADRAO["Vermelho"]


def test_saida_com_dose_do_llm_cai_no_padrao(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "chave-de-teste")
    monkeypatch.setattr(explicacao, "_chamar_llm", lambda _: "O solo está seco. Aplique 30 litros por planta.")
    assert explicacao.gerar_mensagem("Vermelho", LEITURA)[1] == "padrao"


def test_llm_bom_e_usado_e_vai_para_o_cache(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "chave-de-teste")
    chamadas = []

    def ok(mensagens):
        chamadas.append(1)
        return "O solo está mais seco do que o ideal. Vá até a lavoura; a decisão é sua."
    monkeypatch.setattr(explicacao, "_chamar_llm", ok)
    assert explicacao.gerar_mensagem("Vermelho", LEITURA)[1] == "llm"
    assert explicacao.gerar_mensagem("Vermelho", LEITURA)[1] == "llm"
    assert len(chamadas) == 1
