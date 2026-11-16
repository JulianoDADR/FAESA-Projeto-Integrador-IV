"""Diagnostico do Turso (scripts/verificar_turso.py) exercitado com SQLite local: sem rede e sem credenciais reais."""
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import create_engine, func, select, text

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import verificar_turso as vt  # noqa: E402

from app import banco  # noqa: E402

AGORA = datetime(2026, 11, 15, 18, 0, tzinfo=timezone.utc)


@pytest.fixture
def motor_vazio(tmp_path):
    motor = create_engine(f"sqlite:///{(tmp_path / 'vazio.db').as_posix()}")
    yield motor
    motor.dispose()


def test_conexao_em_banco_vazio_nao_e_falha_e_nao_cria_tabelas(motor_vazio, capsys):
    r = vt.verificar_conexao(motor_vazio)
    assert r["conexao"] is True and r["tabelas_faltando"] == ["leituras", "rejeicoes"]
    assert "não é falha de conexão" in capsys.readouterr().out
    with motor_vazio.connect() as c:  # somente leitura: nada foi criado
        assert c.execute(text("SELECT COUNT(*) FROM sqlite_master")).scalar_one() == 0


def test_estrutura_falha_em_banco_vazio_e_passa_com_o_modelo(motor_vazio):
    assert vt.verificar_estrutura(motor_vazio)["estrutura_valida"] is False
    banco.Base.metadata.create_all(motor_vazio)
    r = vt.verificar_estrutura(motor_vazio)
    assert r["estrutura_valida"] is True, r["problemas"]


def test_estrutura_detecta_restricao_unica_ausente(motor_vazio):
    with motor_vazio.begin() as c:
        c.execute(text("CREATE TABLE leituras (id INTEGER PRIMARY KEY, talhao_id TEXT, coletado_em TEXT)"))
        c.execute(text("CREATE INDEX ix_leituras_talhao_id ON leituras (talhao_id)"))
        c.execute(text("CREATE INDEX ix_leituras_coletado_em ON leituras (coletado_em)"))
    r = vt.verificar_estrutura(motor_vazio)
    assert r["estrutura_valida"] is False
    assert any("restrição única" in p for p in r["problemas"])


def test_persistencia_detecta_banco_sem_leituras(motor_vazio):
    banco.Base.metadata.create_all(motor_vazio)
    r = vt.verificar_persistencia(motor_vazio, 72, agora=AGORA)
    assert r["persistencia_valida"] is False and r["total"] == 0


def test_persistencia_detecta_duplicacao_quando_a_restricao_falta(motor_vazio):
    with motor_vazio.begin() as c:  # tabela sem a UniqueConstraint, para simular um banco antigo/corrompido
        c.execute(text("""CREATE TABLE leituras (id INTEGER PRIMARY KEY, talhao_id TEXT, especie TEXT,
            umidade_solo REAL, temperatura REAL, umidade_ar REAL, coletado_em DATETIME, recebido_em DATETIME,
            origem TEXT, valida BOOLEAN)"""))
        for _ in range(2):
            c.execute(text("""INSERT INTO leituras (talhao_id, especie, umidade_solo, temperatura, umidade_ar,
                coletado_em, recebido_em, origem, valida)
                VALUES ('A', 'Arabica', 50, 20, 70, '2026-11-15 17:50:00.000000', '2026-11-15 17:50:00.000000',
                'simulado', 1)"""))
    r = vt.verificar_persistencia(motor_vazio, 24, agora=AGORA)
    assert r["duplicados"] == 1 and r["persistencia_valida"] is False


def test_semear_e_comprovar_cria_tabelas_e_repeticao_nao_duplica(tmp_path):
    url = f"sqlite:///{(tmp_path / 'novo.db').as_posix()}"
    banco.configurar(url)  # o mesmo create_all que o modo semear usa
    r = vt.semear_e_comprovar(24, agora=AGORA)
    assert r["primeira"]["gravadas"] > 0 and r["segunda"]["gravadas"] == 0 and r["repeticao_ok"] is True
    motor = banco.configurar()
    assert vt.verificar_estrutura(motor)["estrutura_valida"] is True
    p = vt.verificar_persistencia(motor, 24, agora=r["agora"], esperado_minimo=r["esperado"])
    assert p["persistencia_valida"] is True and p["duplicados"] == 0
    assert set(p["por_origem"]) == {"simulado"} and p["total"] == r["esperado"]
    with banco.sessao() as s:
        assert s.scalar(select(func.count()).select_from(banco.Leitura)) == r["esperado"]


def test_modo_semear_sem_confirmacao_e_recusado_antes_de_conectar(monkeypatch, capsys):
    monkeypatch.setattr(banco, "resolver_conexao", lambda *_: pytest.fail("não deveria conectar"))
    assert vt.main(["--modo", "semear", "--horas", "24"]) == 2
    assert "--confirmar-escrita" in capsys.readouterr().out


@pytest.mark.parametrize("horas", ["12", "1000", "72; rm -rf /", "abc"])
def test_horas_fora_da_lista_sao_recusadas(horas):
    with pytest.raises(SystemExit) as erro:
        vt.main(["--modo", "persistencia", "--horas", horas])
    assert erro.value.code == 2


def test_diagnostico_recusa_sqlite_local(monkeypatch, capsys):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///qualquer.db")
    assert vt.main(["--modo", "conexao"]) == 1
    assert "espera o Turso" in capsys.readouterr().out


def test_mensagens_nao_vazam_token_nem_url(monkeypatch, capsys):
    monkeypatch.setenv("TURSO_DATABASE_URL", "libsql://banco-ficticio.turso.io")
    monkeypatch.setenv("TURSO_AUTH_TOKEN", "token-ficticio-de-teste")

    def explodir(url, token):
        raise RuntimeError(f"falhou em {url} com {token}")

    monkeypatch.setattr(banco, "criar_motor", explodir)
    assert vt.main(["--modo", "conexao"]) == 1
    saida = capsys.readouterr().out
    assert "token-ficticio-de-teste" not in saida and "libsql://" not in saida and "sqlite+libsql://" not in saida
    assert "RuntimeError" in saida
