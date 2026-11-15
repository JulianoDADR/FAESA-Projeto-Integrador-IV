import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import explicacao  # noqa: E402
from app.principal import app  # noqa: E402


@pytest.fixture(autouse=True)
def isolar_llm(monkeypatch):
    """Nenhum teste chama a rede: sem chave por padrao e cache limpo."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    explicacao.limpar_cache()
    explicacao.zerar_uso()


@pytest.fixture(autouse=True)
def isolar_protecoes(monkeypatch):
    """Modo demonstracao ligado por padrao nos testes (os que testam o desligado removem a variavel)
    e limitador de requisicoes zerado a cada teste."""
    from app import seguranca
    monkeypatch.setenv("MODO_DEMO", "1")
    for variavel in ("ORIGENS_PERMITIDAS", "ALIMENTADOR_DEMO", "SEMEAR_SE_VAZIO", "GROQ_MAX_POR_MINUTO", "GROQ_MAX_POR_DIA"):
        monkeypatch.delenv(variavel, raising=False)
    app.state.limitador = seguranca.LimitadorDeTaxa()


@pytest.fixture(autouse=True)
def isolar_banco_e_fonte(tmp_path, monkeypatch):
    """Cada teste usa um banco SQLite temporario e a fonte simulada (nunca o banco real em dados/)."""
    from app import banco, fontes
    for variavel in ("TOKEN_DISPOSITIVO", "FONTE_LEITURAS", "MINUTOS_DESATUALIZADO", "INTERVALO_LEITURA_MIN"):
        monkeypatch.delenv(variavel, raising=False)
    banco.configurar(f"sqlite:///{(tmp_path / 'teste.db').as_posix()}")
    fontes.definir_fonte(None)
    yield
    fontes.definir_fonte(None)


@pytest.fixture
def cliente():
    return TestClient(app)


@pytest.fixture
def leitura_valida():
    return {"especie": "Arabica", "umidade_solo": 55, "temperatura": 21, "umidade_ar": 72}
