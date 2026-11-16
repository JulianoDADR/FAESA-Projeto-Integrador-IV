"""Diagnostico do Turso/libSQL configurado por variavel de ambiente (TURSO_DATABASE_URL + TURSO_AUTH_TOKEN).

Uso (dentro de prototipo/):
  python scripts/verificar_turso.py --modo conexao        # SELECT 1 e informa se as tabelas existem (SEM escrita)
  python scripts/verificar_turso.py --modo estrutura      # exige tabelas, indices e restricao unica (SEM escrita)
  python scripts/verificar_turso.py --modo persistencia --horas 72   # conta registros na janela (SEM escrita)
  python scripts/verificar_turso.py --modo semear --horas 72 --confirmar-escrita   # ESCREVE no banco

Modos de leitura nunca criam tabelas nem gravam. A ausencia de tabelas no modo `conexao` e informada, mas NAO e
falha: um banco Turso novo ainda nao foi inicializado. O modo `semear` exige `--confirmar-escrita`: cria as tabelas
inexistentes com o modelo SQLAlchemy (app/banco.py), grava leituras SIMULADAS (origem = "simulado") e repete a
semeadura com o mesmo instante para comprovar que a UniqueConstraint (talhao_id, coletado_em) impede duplicacao.

Pensado para o GitHub Actions (Ubuntu): no Windows local o driver libSQL nao e instalado. Nunca imprime o token nem
a URL completa (so o host). Codigo de saida 0 = sucesso; 1 = falha; 2 = uso incorreto.
"""
import argparse
import re
import sys
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app import banco  # noqa: E402

HORAS_PERMITIDAS = (24, 48, 72)
TABELAS = ("leituras", "rejeicoes")
INDICES = {
    "leituras": ("ix_leituras_talhao_id", "ix_leituras_coletado_em"),
    "rejeicoes": ("ix_rejeicoes_talhao_id", "ix_rejeicoes_recebido_em"),
}
ORIGENS_VALIDAS = {"simulado", "dispositivo"}


def _ok(mensagem):
    print(f"[OK ] {mensagem}")


def _falha(mensagem):
    print(f"[FALHOU] {mensagem}")


def _aviso(mensagem):
    print(f"[AVISO] {mensagem}")


def mensagem_segura(erro, *segredos):
    """Texto do erro sem token/URL (o driver pode repetir a URL na mensagem). Limitado a 200 caracteres."""
    texto = str(erro)
    for segredo in segredos:
        if segredo:
            texto = texto.replace(segredo, "***")
    return re.sub(r"(libsql|https?|wss?)://\S+", "***", texto)[:200]


def tabelas_existentes(conexao):
    linhas = conexao.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
    return {nome for (nome,) in linhas}


def verificar_conexao(motor):
    """SELECT 1 e informa quais tabelas existem. Nao escreve. Falha so se a conexao falhar."""
    with motor.connect() as conexao:
        conexao.execute(text("SELECT 1")).scalar_one()
        _ok("Conexão válida (SELECT 1)")
        existentes = tabelas_existentes(conexao)
    faltando = [t for t in TABELAS if t not in existentes]
    if faltando:
        _aviso(f"Banco ainda não inicializado: tabela(s) ausente(s): {', '.join(faltando)}. "
               "Isso não é falha de conexão; rode a semeadura autorizada para criar a estrutura.")
    else:
        _ok("Tabelas leituras e rejeicoes existem")
    return {"conexao": True, "tabelas_faltando": faltando}


def _restricao_unica_presente(conexao):
    """Procura a restricao unica (talhao_id, coletado_em) pela definicao da tabela ou por um indice unico."""
    sql = conexao.execute(text("SELECT sql FROM sqlite_master WHERE type='table' AND name='leituras'")).scalar() or ""
    normalizado = re.sub(r"\s+", "", sql.lower())
    if "unique(talhao_id,coletado_em)" in normalizado:
        return True
    indices = conexao.execute(text("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='leituras'"))
    for (definicao,) in indices:
        d = re.sub(r"\s+", "", (definicao or "").lower())
        if d.startswith("createuniqueindex") and "(talhao_id,coletado_em)" in d:
            return True
    return False


def verificar_estrutura(motor):
    """Exige tabelas, indices e a restricao unica. Nao escreve."""
    problemas = []
    with motor.connect() as conexao:
        existentes = tabelas_existentes(conexao)
        for tabela in TABELAS:
            if tabela not in existentes:
                problemas.append(f"tabela {tabela} não existe")
                continue
            _ok(f"Estrutura: tabela {tabela} existe")
            indices = {nome for (nome,) in conexao.execute(
                text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name=:t"), {"t": tabela})}
            for indice in INDICES[tabela]:
                if indice in indices:
                    _ok(f"Estrutura: índice {indice}")
                else:
                    problemas.append(f"índice {indice} ausente")
        if "leituras" in existentes:
            if _restricao_unica_presente(conexao):
                _ok("Estrutura: restrição única (talhao_id, coletado_em) presente")
            else:
                problemas.append("restrição única (talhao_id, coletado_em) ausente em leituras")
    for problema in problemas:
        _falha(f"Estrutura: {problema}")
    return {"estrutura_valida": not problemas, "problemas": problemas}


def verificar_persistencia(motor, horas, agora=None, esperado_minimo=None):
    """Conta registros na janela, por origem, e procura duplicados (talhao_id, coletado_em). Nao escreve."""
    agora = agora or banco.agora_utc()
    inicio = agora - timedelta(hours=horas)
    L = banco.Leitura
    with Session(motor) as s:
        na_janela = (L.coletado_em > inicio) & (L.coletado_em <= agora)
        total_geral = s.scalar(select(func.count()).select_from(L))
        total = s.scalar(select(func.count()).select_from(L).where(na_janela))
        por_origem = dict(s.execute(select(L.origem, func.count()).where(na_janela).group_by(L.origem)).all())
        duplicados = s.scalar(select(func.count()).select_from(
            select(L.talhao_id, L.coletado_em).group_by(L.talhao_id, L.coletado_em)
            .having(func.count() > 1).subquery()))
    problemas = []
    print(f"[INFO] Leituras no banco: {total_geral}; na janela de {horas} h: {total}; por origem: {por_origem}")
    if total == 0:
        problemas.append(f"nenhuma leitura na janela de {horas} h")
    if esperado_minimo is not None and total < esperado_minimo:
        problemas.append(f"esperado ao menos {esperado_minimo} leitura(s) na janela, encontrado {total}")
    origens_invalidas = set(por_origem) - ORIGENS_VALIDAS
    if origens_invalidas:
        problemas.append(f"origem fora do esperado: {sorted(origens_invalidas)}")
    if duplicados:
        problemas.append(f"{duplicados} par(es) (talhao_id, coletado_em) duplicado(s)")
    else:
        _ok("Sem duplicações de (talhao_id, coletado_em)")
    if not problemas:
        _ok(f"Persistência comprovada: {total} leitura(s) na janela ({por_origem.get('simulado', 0)} simulada(s))")
    for problema in problemas:
        _falha(f"Persistência: {problema}")
    return {"persistencia_valida": not problemas, "total": total, "por_origem": por_origem,
            "duplicados": duplicados, "problemas": problemas}


def semear_e_comprovar(horas, agora=None):
    """ESCREVE: cria tabelas inexistentes (banco.configurar), semeia e repete no mesmo instante.

    Usa o banco ja configurado em `banco` (a funcao main chama banco.configurar()).
    """
    from app.semear import _alinhar_grade, semear
    from app.indicadores import intervalo_leitura_min

    intervalo = int(intervalo_leitura_min())
    agora = _alinhar_grade(agora or banco.agora_utc(), intervalo)
    primeira = semear(horas, agora=agora, intervalo_min=intervalo)
    _ok(f"Semeadura 1: {primeira['gravadas']} gravada(s), {primeira['ignoradas']} já existente(s) (origem = simulado)")
    segunda = semear(horas, agora=agora, intervalo_min=intervalo)
    esperado = primeira["gravadas"] + primeira["ignoradas"]
    repeticao_ok = segunda["gravadas"] == 0 and segunda["ignoradas"] == esperado
    if repeticao_ok:
        _ok(f"Semeadura 2 (mesma janela): 0 gravada(s), {segunda['ignoradas']} ignorada(s) -> idempotente")
    else:
        _falha(f"Semeadura 2 (mesma janela) gravou {segunda['gravadas']} e ignorou {segunda['ignoradas']} "
               f"(esperado 0 e {esperado})")
    return {"primeira": primeira, "segunda": segunda, "repeticao_ok": repeticao_ok, "agora": agora,
            "esperado": esperado}


def _ler_argumentos(argv):
    p = argparse.ArgumentParser(description="Diagnóstico do Turso/libSQL (sem expor credenciais).")
    p.add_argument("--modo", choices=("conexao", "estrutura", "persistencia", "semear"), default="conexao")
    p.add_argument("--horas", type=int, default=72, choices=HORAS_PERMITIDAS)
    p.add_argument("--confirmar-escrita", action="store_true",
                   help="obrigatório no modo semear: autoriza criar tabelas e gravar leituras simuladas")
    return p.parse_args(argv)


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    opcoes = _ler_argumentos(argv)
    if opcoes.modo == "semear" and not opcoes.confirmar_escrita:
        _falha("O modo semear grava no banco e exige --confirmar-escrita.")
        return 2
    try:
        url, token = banco.resolver_conexao()
    except Exception as erro:
        _falha(f"Configuração do banco ({type(erro).__name__}). Confira TURSO_DATABASE_URL e TURSO_AUTH_TOKEN.")
        return 1
    if not url.startswith("sqlite+libsql://"):
        _falha("Este diagnóstico espera o Turso/libSQL (TURSO_DATABASE_URL libsql://...).")
        return 1
    _ok(f"Destino: {urlsplit(url).hostname or '(sem host)'} (token configurado: {'sim' if token else 'não'})")
    print(f"[INFO] Modo: {opcoes.modo} ({'ESCRITA autorizada' if opcoes.modo == 'semear' else 'somente leitura'})")

    motor = None
    try:
        motor = banco.criar_motor(url, token)
        verificar_conexao(motor)
        if opcoes.modo == "conexao":
            return 0
        if opcoes.modo == "estrutura":
            return 0 if verificar_estrutura(motor)["estrutura_valida"] else 1
        if opcoes.modo == "persistencia":
            return 0 if verificar_persistencia(motor, opcoes.horas)["persistencia_valida"] else 1

        motor.dispose()
        motor = None
        banco.configurar()  # cria SOMENTE as tabelas/indices inexistentes (create_all nao apaga nem altera)
        _ok("Tabelas inexistentes criadas pelo modelo SQLAlchemy (as existentes foram preservadas)")
        resultado = semear_e_comprovar(opcoes.horas)
        estrutura = verificar_estrutura(banco.configurar())
        persistencia = verificar_persistencia(banco.configurar(), opcoes.horas, agora=resultado["agora"],
                                              esperado_minimo=resultado["esperado"])
        tudo_ok = resultado["repeticao_ok"] and estrutura["estrutura_valida"] and persistencia["persistencia_valida"]
        print("[OK ] Semeadura comprovada" if tudo_ok else "[FALHOU] Semeadura não comprovada")
        return 0 if tudo_ok else 1
    except Exception as erro:
        _falha(f"Não foi possível acessar o Turso ({type(erro).__name__}: {mensagem_segura(erro, token, url)}).")
        return 1
    finally:
        if motor is not None:
            motor.dispose()
        banco.fechar()


if __name__ == "__main__":
    raise SystemExit(main())
