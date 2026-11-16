"""Prova do driver/dialeto libSQL com arquivo local (sem Turso remoto, sem rede, sem credenciais).

No Windows local o driver nao e instalado (marcador `sys_platform != "win32"` no requirements.txt): o modulo inteiro
e pulado de forma explicita. Em Linux/macOS (GitHub Actions/Ubuntu) a ausencia de `libsql_experimental` ou
`sqlalchemy_libsql` e FALHA, nao skip: a CI precisa provar que o driver do deploy funciona.
"""
import importlib
import sys
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.orm import Session

from app import banco

pytestmark = pytest.mark.skipif(sys.platform == "win32",
                                reason="driver libSQL não é instalado no Windows local (validado na CI Ubuntu)")

INSTANTE = datetime(2026, 11, 15, 18, 0, tzinfo=timezone.utc)


def _url(caminho):
    return f"sqlite+libsql:///{caminho.as_posix()}?secure=false"


def _leitura(**extra):
    dados = dict(talhao_id="A", especie="Arabica", umidade_solo=55.0, temperatura=21.0, umidade_ar=72.0,
                 coletado_em=INSTANTE, recebido_em=INSTANTE, origem="simulado", valida=True)
    dados.update(extra)
    return banco.Leitura(**dados)


@pytest.mark.parametrize("modulo", ["libsql_experimental", "sqlalchemy_libsql"])
def test_driver_libsql_esta_instalado(modulo):
    # importlib.import_module (e nao importorskip): ausencia do pacote derruba o teste na CI
    assert importlib.import_module(modulo) is not None


def test_dialeto_sqlite_libsql_carrega(tmp_path):
    motor = create_engine(_url(tmp_path / "dialeto.db"))
    try:
        assert motor.dialect.name == "sqlite"
        assert getattr(motor.dialect, "driver", "") == "libsql"
        with motor.connect() as conexao:
            assert conexao.execute(text("SELECT 1")).scalar_one() == 1
    finally:
        motor.dispose()


def test_criar_inserir_consultar_e_reabrir(tmp_path):
    caminho = tmp_path / "ciclo.db"
    motor = create_engine(_url(caminho))
    try:
        banco.Base.metadata.create_all(motor)
        with motor.connect() as conexao:
            tabelas = {n for (n,) in conexao.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}
        assert {"leituras", "rejeicoes"} <= tabelas

        with Session(motor) as s:
            s.add(_leitura())
            s.commit()
        with Session(motor) as s:
            lida = s.scalars(select(banco.Leitura)).one()
            assert (lida.talhao_id, lida.umidade_solo, lida.origem) == ("A", 55.0, "simulado")
            assert lida.coletado_em == INSTANTE  # InstanteUTC devolve com fuso UTC tambem no libSQL
    finally:
        motor.dispose()

    reaberto = create_engine(_url(caminho))
    try:
        with Session(reaberto) as s:
            assert s.scalar(select(func.count()).select_from(banco.Leitura)) == 1
            assert s.scalars(select(banco.Leitura.talhao_id)).one() == "A"
    finally:
        reaberto.dispose()


def test_erros_do_driver_sao_levantados_e_nao_corrompem_os_dados(tmp_path):
    motor = create_engine(_url(tmp_path / "erros.db"))
    try:
        banco.Base.metadata.create_all(motor)
        with Session(motor) as s:
            s.add(_leitura())
            s.commit()
        with Session(motor) as s:  # UniqueConstraint (talhao_id, coletado_em) vale tambem no libSQL
            s.add(_leitura(umidade_solo=10.0))
            with pytest.raises(Exception):
                s.commit()
            s.rollback()
        with motor.connect() as conexao:
            with pytest.raises(Exception):
                conexao.execute(text("SELECT * FROM tabela_que_nao_existe"))
        with Session(motor) as s:
            assert s.scalar(select(func.count()).select_from(banco.Leitura)) == 1
            assert s.scalars(select(banco.Leitura.umidade_solo)).one() == 55.0
    finally:
        motor.dispose()


def test_modulo_banco_configura_libsql_local_e_verifica(tmp_path, monkeypatch):
    """Caminho real da aplicacao (banco.configurar + verificar + sessao) usando o driver libSQL."""
    monkeypatch.delenv("TURSO_AUTH_TOKEN", raising=False)
    banco.configurar(_url(tmp_path / "app.db"))
    assert banco.descrever_url() == "libsql" and banco.verificar() is True
    with banco.sessao() as s:
        s.add(_leitura())
        s.commit()
    assert banco.contar_leituras() == 1
