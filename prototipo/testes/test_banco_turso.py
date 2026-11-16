"""Configuracao do banco: Turso/libSQL, fail-soft da demonstracao e diagnostico sem vazar credenciais."""
import pytest
from fastapi.testclient import TestClient

from app import alimentador, banco, fontes
from app.principal import app, criar_app


def test_normalizar_url_do_painel_do_turso():
    assert banco.normalizar_url("libsql://exemplo.turso.io") == "sqlite+libsql://exemplo.turso.io?secure=true"
    assert banco.normalizar_url("https://exemplo.turso.io") == "sqlite+libsql://exemplo.turso.io?secure=true"
    assert banco.normalizar_url("http://127.0.0.1:8080") == "sqlite+libsql://127.0.0.1:8080?secure=false"
    assert banco.normalizar_url("postgres://u:p@host/db") == "postgresql://u:p@host/db"
    assert banco.normalizar_url("sqlite+libsql://exemplo.turso.io?secure=true") == \
        "sqlite+libsql://exemplo.turso.io?secure=true"
    assert banco.normalizar_url("sqlite:///dados/agroanalise.db") == "sqlite:///dados/agroanalise.db"


def test_resolver_conexao_prioriza_turso(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://exemplo.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-de-teste")
    url, token = banco.resolver_conexao()
    assert url == "sqlite+libsql://exemplo.turso.io?secure=true" and token == "token-de-teste"
    assert "token-de-teste" not in url


def test_turso_sem_token_falha_cedo(monkeypatch):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://exemplo.turso.io")
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    with pytest.raises(banco.BancoIndisponivel):
        banco.resolver_conexao()


def test_turso_com_token_sem_url_falha_cedo(monkeypatch):
    monkeypatch.delenv("TURSO_DATABASE_URL", raising=False)
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-de-teste")
    with pytest.raises(banco.BancoIndisponivel):
        banco.resolver_conexao()


def test_configurar_sem_url_preserva_conexao_temporaria_ja_configurada(tmp_path):
    url = f"sqlite:///{(tmp_path / 'isolado.db').as_posix()}"
    banco.configurar(url)
    with banco.sessao() as s:
        s.add(banco.Rejeicao(talhao_id="A", recebido_em=banco.agora_utc(), motivo="teste"))
        s.commit()
    banco.configurar()
    with banco.sessao() as s:
        assert s.query(banco.Rejeicao).count() == 1
    assert banco.descrever_url() == "sqlite"


def test_banco_local_da_fixture_esta_disponivel(cliente):
    assert banco.verificar() is True and banco.descrever_url() == "sqlite"
    assert cliente.get("/saude").json()["banco_disponivel"] is True


def test_sem_motor_verificar_nao_quebra():
    banco.fechar()
    assert banco.verificar() is False and banco.descrever_url() is None


def test_startup_fail_soft_com_fonte_simulada(monkeypatch):
    banco.fechar()
    monkeypatch.setattr(banco, "configurar", lambda *_, **__: (_ for _ in ()).throw(
        banco.BancoIndisponivel("banco fora do ar")))
    monkeypatch.setenv("FONTE_LEITURAS", "simulada")
    fontes.definir_fonte(None)
    with TestClient(criar_app()) as c:
        assert c.get("/status").status_code == 200
        assert c.get("/index.html").status_code == 200
        saude = c.get("/saude").json()
        assert saude["banco_disponivel"] is False and saude["fonte_leituras"] == "simulada"
        r = c.get("/disponibilidade")
        assert r.status_code == 503 and "Banco de dados indisponível" in r.json()["erros"][0]


def test_startup_e_fatal_quando_a_fonte_e_o_banco(monkeypatch):
    banco.fechar()
    monkeypatch.setattr(banco, "configurar", lambda *_, **__: (_ for _ in ()).throw(
        banco.BancoIndisponivel("banco fora do ar")))
    monkeypatch.setenv("FONTE_LEITURAS", "banco")
    fontes.definir_fonte(None)
    with pytest.raises(banco.BancoIndisponivel):
        with TestClient(criar_app()):
            pass


def test_alimentador_fica_desligado_na_vercel(monkeypatch):
    monkeypatch.setenv("ALIMENTADOR_DEMO", "1")
    monkeypatch.setenv("VERCEL", "1")
    assert alimentador.ligado() is False


def test_saude_continua_respondendo_com_banco_fora(monkeypatch):
    banco.fechar()
    monkeypatch.setattr(banco, "configurar", lambda *_, **__: (_ for _ in ()).throw(
        banco.BancoIndisponivel("banco fora do ar")))
    c = TestClient(app)
    assert c.get("/saude").status_code == 200 and c.get("/saude").json()["banco_disponivel"] is False


def test_saude_com_turso_configurado_e_fora_do_ar_nao_vaza_credenciais(monkeypatch, caplog):
    """Turso configurado (valores ficticios) mas inacessivel: /saude responde 200, sem token nem URL na resposta/log."""
    banco.fechar()
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://banco-ficticio.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-ficticio-nao-real")
    monkeypatch.setenv("FONTE_LEITURAS", "simulada")
    monkeypatch.setattr(banco, "criar_motor", lambda *_: (_ for _ in ()).throw(
        banco.BancoIndisponivel("conexao recusada")))
    fontes.definir_fonte(None)
    with TestClient(criar_app()) as c:
        r = c.get("/saude")
        assert r.status_code == 200 and r.json()["banco_disponivel"] is False
        assert c.get("/status").status_code == 200  # semaforo simulado segue no ar (fail-soft)
        texto = r.text + c.get("/disponibilidade").text
    assert "token-ficticio-nao-real" not in texto + caplog.text
    assert "banco-ficticio" not in texto + caplog.text


def test_post_leituras_com_token_valido_e_banco_fora_responde_503(monkeypatch):
    banco.fechar()
    monkeypatch.setenv("TOKEN_DISPOSITIVO", "token-de-teste-123")
    monkeypatch.setattr(banco, "configurar", lambda *_, **__: (_ for _ in ()).throw(
        banco.BancoIndisponivel("banco fora do ar")))
    c = TestClient(app)
    r = c.post("/leituras", headers={"Authorization": "Bearer token-de-teste-123"},
               json={"talhao_id": "A", "coletado_em": banco.agora_utc().isoformat(), "umidade_solo": 50,
                     "temperatura": 21, "umidade_ar": 70, "origem": "simulado"})
    assert r.status_code == 503 and r.headers["Retry-After"] == "5"
    assert "token-de-teste-123" not in r.text
