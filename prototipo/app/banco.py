"""Banco da aplicacao (SQLAlchemy). SQLite local por padrao e Turso/libSQL no deploy.

A ordem de configuracao e: `TURSO_DATABASE_URL` + `TURSO_AUTH_TOKEN` (deploy), `DATABASE_URL` (SQLite ou outro banco
suportado) e, por fim, o SQLite local em `prototipo/dados/`. O token do Turso vai somente em `connect_args`; nunca e
gravado na URL, em log ou em arquivo versionado.

Migracao simples: as tabelas sao criadas no startup (metadata.create_all). Nao ha Alembic: o esquema e pequeno e,
se mudar, o grupo recria o banco de demonstracao com a semente (app/semear.py).

No plano gratuito o disco local pode ser apagado a cada reinicio. Por isso o deploy usa o Turso (remoto); sem ele,
o sistema continua com a fonte simulada (fail-soft) quando `FONTE_LEITURAS=simulada`.
"""
import os
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from sqlalchemy import (Boolean, DateTime, Float, Integer, String, UniqueConstraint, create_engine, event, func,
                        select, text)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.types import TypeDecorator

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")
URL_PADRAO = f"sqlite:///{(RAIZ / 'dados' / 'agroanalise.db').as_posix()}"


class BancoIndisponivel(RuntimeError):
    """Banco configurado mas inacessivel. A API responde 503 em vez de derrubar as rotas simuladas."""


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
_url_atual = None
_token_atual = None


def normalizar_url(url):
    """Converte a URL do painel do Turso na URL que o dialeto `sqlite+libsql` entende."""
    url = url.strip()
    seguro = True
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    elif url.startswith("libsql://"):
        url = "sqlite+libsql://" + url[len("libsql://"):]
    elif url.startswith("https://"):
        url = "sqlite+libsql://" + url[len("https://"):]
    elif url.startswith("http://"):  # sqld local, sem TLS
        url = "sqlite+libsql://" + url[len("http://"):]
        seguro = False
    if url.startswith("sqlite+libsql://"):
        partes = urlsplit(url)
        if partes.hostname and "secure=" not in partes.query:
            url += ("&" if partes.query else "?") + f"secure={'true' if seguro else 'false'}"
    return url


def resolver_conexao(url=None):
    """Devolve (url_normalizada, token) sem expor o token. Levanta BancoIndisponivel se a configuração Turso estiver incompleta."""
    if url:
        normalizada = normalizar_url(url)
        token = (os.getenv("TURSO_AUTH_TOKEN") or "").strip() or None
        return normalizada, token if normalizada.startswith("sqlite+libsql://") else None

    turso = (os.getenv("TURSO_DATABASE_URL") or "").strip()
    token = (os.getenv("TURSO_AUTH_TOKEN") or "").strip()
    if turso and not token:
        raise BancoIndisponivel("TURSO_AUTH_TOKEN não configurado para o Turso.")
    if token and not turso:
        raise BancoIndisponivel("TURSO_AUTH_TOKEN configurado sem TURSO_DATABASE_URL; corrija a configuração Turso.")
    if turso:
        return normalizar_url(turso), token

    endereco = (os.getenv("DATABASE_URL") or "").strip() or URL_PADRAO
    normalizada = normalizar_url(endereco)
    return normalizada, token if (token and normalizada.startswith("sqlite+libsql://")) else None


def criar_motor(url, token=None):
    """Cria o motor sem criar tabelas (usado tambem pelo diagnostico somente leitura do Turso)."""
    if os.name == "nt" and url.startswith("sqlite+libsql://"):
        raise BancoIndisponivel(
            "O driver libSQL/Turso não está disponível no Windows local; use SQLite localmente e valide a conexão Turso pelo GitHub Actions (workflow manual) ou em ambiente Linux."
        )
    if url.startswith("sqlite:///"):
        Path(url[len("sqlite:///"):]).parent.mkdir(parents=True, exist_ok=True)
    opcoes = {"auth_token": token} if token and url.startswith("sqlite+libsql://") else {}
    motor = create_engine(url, pool_pre_ping=True, connect_args=opcoes)
    if motor.dialect.name == "sqlite" and getattr(motor.dialect, "driver", "") != "libsql":
        @event.listens_for(motor, "connect")
        def _wal(conexao, _):
            conexao.execute("PRAGMA journal_mode=WAL")  # leitura e escrita ao mesmo tempo (API + gateway)
    return motor


def configurar(url=None):
    """Cria o motor e as tabelas. Repetir com a mesma configuracao nao abre outra conexao."""
    global _motor, _fabrica, _url_atual, _token_atual
    if url is None and _motor is not None:
        return _motor
    url_resolvida, token = resolver_conexao(url)
    if _motor is not None and url_resolvida == _url_atual and token == _token_atual:
        return _motor
    fechar()
    motor = None
    try:
        motor = criar_motor(url_resolvida, token)
        Base.metadata.create_all(motor)
    except Exception:
        if motor is not None:
            motor.dispose()
        raise
    _motor, _fabrica = motor, sessionmaker(motor, expire_on_commit=False)
    _url_atual, _token_atual = url_resolvida, token
    return _motor


def fechar():
    """Fecha o pool e esquece a configuracao (shutdown e testes)."""
    global _motor, _fabrica, _url_atual, _token_atual
    if _motor is not None:
        _motor.dispose()
    _motor = _fabrica = _url_atual = _token_atual = None


def sessao() -> Session:
    if _fabrica is None:
        configurar()
    return _fabrica()


def descrever_url():
    """Nome do banco sem credenciais (para /saude e logs)."""
    if _motor is None:
        return None
    return "libsql" if getattr(_motor.dialect, "driver", "") == "libsql" else _motor.dialect.name


def verificar():
    """Testa a conexao com SELECT 1. Nunca levanta excecao (usado em /saude)."""
    if _motor is None:
        return False
    try:
        with _motor.connect() as conexao:
            conexao.execute(text("SELECT 1"))
        return True
    except Exception:  # driver remoto pode levantar erro proprio; /saude nunca deve quebrar
        return False


def contar_leituras():
    with sessao() as s:
        return s.scalar(select(func.count()).select_from(Leitura))


def agora_utc():
    return datetime.now(timezone.utc)
