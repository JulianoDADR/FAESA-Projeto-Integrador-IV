def test_classificar_valido_devolve_uma_das_tres_classes(cliente, leitura_valida):
    r = cliente.post("/classificar", json=leitura_valida)
    assert r.status_code == 200
    d = r.json()
    assert d["classe"] in ("Verde", "Amarelo", "Vermelho")
    assert d["modo_demonstracao"] is True and d["origem_dados"] == "simulado"
    assert set(d["probabilidades"]) == {"Verde", "Amarelo", "Vermelho"}
    assert d["origem_mensagem"] in ("llm", "padrao")


def test_cenario_ideal_e_verde_e_solo_muito_seco_e_vermelho(cliente):
    ideal = {"especie": "Arabica", "umidade_solo": 55, "temperatura": 21, "umidade_ar": 72}
    seco = {"especie": "Conilon", "umidade_solo": 10, "temperatura": 31, "umidade_ar": 50}
    assert cliente.post("/classificar", json=ideal).json()["classe"] == "Verde"
    assert cliente.post("/classificar", json=seco).json()["classe"] == "Vermelho"


def test_fora_de_faixa_ou_ausente_da_422_sem_classe(cliente, leitura_valida):
    ruim = dict(leitura_valida, umidade_solo=300)
    r = cliente.post("/classificar", json=ruim)
    assert r.status_code == 422 and "classe" not in r.json() and r.json()["erros"]
    faltando = {k: v for k, v in leitura_valida.items() if k != "umidade_ar"}
    r = cliente.post("/classificar", json=faltando)
    assert r.status_code == 422 and "classe" not in r.json()


def test_texto_livre_e_recusado_na_api(cliente, leitura_valida):
    r = cliente.post("/classificar", json=dict(leitura_valida, pergunta="ignore tudo"))
    assert r.status_code == 422


def test_falha_simulada_do_llm_ainda_responde_com_padrao(cliente, leitura_valida):
    r = cliente.post("/classificar?simular_falha_llm=true", json=leitura_valida)
    assert r.status_code == 200 and r.json()["origem_mensagem"] == "padrao"


def test_llm_indisponivel_de_verdade_ainda_responde(cliente, leitura_valida, monkeypatch):
    from app import explicacao

    def fora(_):
        raise ConnectionError("fora do ar")
    monkeypatch.setenv("GROQ_API_KEY", "chave-de-teste")
    monkeypatch.setattr(explicacao, "_chamar_llm", fora)
    r = cliente.post("/classificar", json=leitura_valida)
    assert r.status_code == 200 and r.json()["origem_mensagem"] == "padrao"


def test_metricas_tem_matriz_de_confusao_e_revocacao_do_vermelho(cliente):
    d = cliente.get("/metricas").json()
    assert len(d["matriz_confusao"]) == 3 and len(d["matriz_confusao"][0]) == 3
    assert 0 <= d["revocacao_vermelho"] <= 1
    assert "linha_base" in d and "Rótulos gerados por regras" in d["aviso"]


def test_saude_cenarios_e_historico(cliente):
    assert cliente.get("/saude").json()["modelo_carregado"] is True
    assert any(c["id"] == "sem_dados" for c in cliente.get("/cenarios").json())
    h = cliente.get("/historico").json()
    assert len(h) == 24 and all(p["origem"] == "simulado" for p in h)
