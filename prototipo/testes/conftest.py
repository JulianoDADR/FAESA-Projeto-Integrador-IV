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


@pytest.fixture
def cliente():
    return TestClient(app)


@pytest.fixture
def leitura_valida():
    return {"especie": "Arabica", "umidade_solo": 55, "temperatura": 21, "umidade_ar": 72}
