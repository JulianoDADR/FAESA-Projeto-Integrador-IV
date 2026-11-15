"""Banco da aplicacao (SQLAlchemy). DATABASE_URL escolhe o banco: SQLite local por padrao, Postgres gerenciado no deploy.

Migracao simples: as tabelas sao criadas no startup (metadata.create_all). Nao ha Alembic: o esquema e pequeno e,
se mudar, o grupo recria o banco de demonstracao com a semente (app/semear.py).

ATENCAO (deploy gratuito): o disco de servicos gratuitos pode ser apagado a cada reinicio. Um SQLite na nuvem pode
perder todo o historico; por isso o deploy deve usar um Postgres gerenciado (ver docs/DEPLOY.md na Etapa 5).
"""
import os
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (Boolean, DateTime, Float, Integer, String, UniqueConstraint, create_engine, event, func,
                        select)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.types import TypeDecorator

RAIZ = Path(__file__).resolve().parent.parent
URL_PADRAO = f"sqlite:///{(RAIZ / 'dados' / 'agroanalise.db').as_posix()}"


class InstanteUTC(TypeDecorator):
    """Guarda sempre em UTC e devolve com fuso (o SQLite nao guarda fuso sozinho)."""
    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, valor, dialeto):
        if valor is None:
            return None
        if valor.tzinfo is None:
            raise ValueError("instante sem fuso horário")
        return valor.astimezone(timezone.utc).replace(tzinfo=None) if dialeto.name == "sqlite" else valor

    def process_result_value(self, valor, dialeto):
        if valor is None:
            return None
        return valor.replace(tzinfo=timezone.utc) if valor.tzinfo is None else valor.astimezone(timezone.utc)


class Base(DeclarativeBase):
    pass


class Leitura(Base):
    """Uma leitura valida de um ponto de monitoramento. So leituras aprovadas na validacao entram aqui."""
    __tablename__ = "leituras"
    __table_args__ = (UniqueConstraint("talhao_id", "coletado_em", name="uq_leitura_talhao_instante"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    talhao_id: Mapped[str] = mapped_column(String(16), index=True)
    especie: Mapped[str] = mapped_column(String(16))
    umidade_solo: Mapped[float] = mapped_column(Float)
    temperatura: Mapped[float] = mapped_column(Float)
    umidade_ar: Mapped[float] = mapped_column(Float)
    coletado_em: Mapped[datetime] = mapped_column(InstanteUTC, index=True)
    recebido_em: Mapped[datetime] = mapped_column(InstanteUTC)
    origem: Mapped[str] = mapped_column(String(16))  # "simulado" ou "dispositivo"
    valida: Mapped[bool] = mapped_column(Boolean, default=True)


class Rejeicao(Base):
    """Tentativa de envio recusada por valor fora do possivel (para o indicador de disponibilidade)."""
    __tablename__ = "rejeicoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    talhao_id: Mapped[str] = mapped_column(String(16), index=True)
    recebido_em: Mapped[datetime] = mapped_column(InstanteUTC, index=True)
    motivo: Mapped[str] = mapped_column(String(300))


_motor = None
_fabrica = None


def configurar(url=None):
    """Cria o motor e as tabelas. Chamado no startup da API e nos testes (com um banco temporario)."""
    global _motor, _fabrica
    url = url or os.getenv("DATABASE_URL") or URL_PADRAO
    if url.startswith("postgres://"):  # alguns provedores ainda usam o prefixo antigo
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("sqlite:///"):
        Path(url[len("sqlite:///"):]).parent.mkdir(parents=True, exist_ok=True)
    _motor = create_engine(url, pool_pre_ping=True)
    if _motor.dialect.name == "sqlite":
        @event.listens_for(_motor, "connect")
        def _wal(conexao, _):
            conexao.execute("PRAGMA journal_mode=WAL")  # leitura e escrita ao mesmo tempo (API + gateway)
    Base.metadata.create_all(_motor)
    _fabrica = sessionmaker(_motor, expire_on_commit=False)
    return _motor


def sessao() -> Session:
    if _fabrica is None:
        configurar()
    return _fabrica()


def descrever_url():
    """Nome do banco sem credenciais (para /saude e logs)."""
    if _motor is None:
        return None
    return _motor.dialect.name


def contar_leituras():
    with sessao() as s:
        return s.scalar(select(func.count()).select_from(Leitura))


def agora_utc():
    return datetime.now(timezone.utc)
