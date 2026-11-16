"""Calcula os indicadores de impacto do relatorio (secao 9.2, Quadro 5) a partir de dados REAIS coletados.

Uso (dentro de prototipo/):
  python ml/calcular_indicadores.py                                    # planilha padrao, sem disponibilidade
  python ml/calcular_indicadores.py --url https://<url-publica>        # tambem le /disponibilidade da API
  python ml/calcular_indicadores.py --planilha caminho.csv --saida pasta/

Gera indicadores.md e indicadores.json (padrao: docs/usabilidade/). Nada e inventado: sem participantes, o
indicador aparece como "sem dados"; sem --url, a disponibilidade aparece como "nao medida".

Planilha (docs/usabilidade/planilha_coleta.csv), uma linha por participante:
  codigo (P01...), data, consentiu (sim/nao), perfil (produtor | tecnico | baixo_letramento | outro: categoria,
  nunca dado pessoal), dispositivo, tarefaN_ok e tarefaN_ajuda (sim/nao, N = 1..3), tempo_total_s,
  extra_e1_ok, extra_e2_ok (sim/nao, opcionais), clareza_1a5 (1 a 5), observacoes.
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd

RAIZ = Path(__file__).resolve().parent.parent
PLANILHA_PADRAO = RAIZ.parent / "docs" / "usabilidade" / "planilha_coleta.csv"
SAIDA_PADRAO = RAIZ.parent / "docs" / "usabilidade"
METAS = {"adocao_autonoma": 0.70, "clareza_4_ou_5": 0.80, "disponibilidade_72h": 0.95, "revocacao_vermelho": 0.90}
MINIMO_PARTICIPANTES = 10
TEMPO_MAXIMO_S = 300


def _sim(serie):
    return serie.astype(str).str.strip().str.lower().isin(["sim", "s", "1", "true"])


def adocao_e_clareza(planilha):
    dados = pd.read_csv(planilha, dtype=str).fillna("")
    dados = dados[_sim(dados["consentiu"])] if len(dados) else dados
    n = len(dados)
    if n == 0:
        return {"participantes": 0, "adocao_autonoma": None, "clareza_4_ou_5": None, "aviso": "sem participantes ainda"}
    tempo = pd.to_numeric(dados["tempo_total_s"], errors="coerce")
    concluiu = _sim(dados["tarefa1_ok"]) & _sim(dados["tarefa2_ok"]) & _sim(dados["tarefa3_ok"])
    sem_ajuda = ~(_sim(dados["tarefa1_ajuda"]) | _sim(dados["tarefa2_ajuda"]) | _sim(dados["tarefa3_ajuda"]))
    autonomos = concluiu & sem_ajuda & (tempo <= TEMPO_MAXIMO_S)
    notas = pd.to_numeric(dados["clareza_1a5"], errors="coerce").dropna()
    notas = notas[(notas >= 1) & (notas <= 5)]
    resultado = {
        "participantes": n,
        "minimo_atingido": n >= MINIMO_PARTICIPANTES,
        "autonomos": int(autonomos.sum()),
        "adocao_autonoma": round(float(autonomos.mean()), 4),
        "respostas_clareza": int(len(notas)),
        "clareza_4_ou_5": round(float((notas >= 4).mean()), 4) if len(notas) else None,
        "clareza_media": round(float(notas.mean()), 2) if len(notas) else None,
        "por_tarefa": {f"tarefa{i}": {"concluiram": int(_sim(dados[f"tarefa{i}_ok"]).sum()),
                                      "precisaram_de_ajuda": int(_sim(dados[f"tarefa{i}_ajuda"]).sum())} for i in (1, 2, 3)},
        "perfis": dados["perfil"].replace("", "não informado").value_counts().to_dict(),
    }
    for extra in ("extra_e1_ok", "extra_e2_ok"):
        if extra in dados and (dados[extra] != "").any():
            respondidas = dados[dados[extra] != ""]
            resultado[extra] = {"respostas": int(len(respondidas)), "concluiram": int(_sim(respondidas[extra]).sum())}
    if n < MINIMO_PARTICIPANTES:
        resultado["aviso"] = f"apenas {n} participantes; a meta pede pelo menos {MINIMO_PARTICIPANTES}"
    return resultado


def disponibilidade(url):
    if not url:
        return {"disponibilidade_72h": None, "aviso": "não medida (rode com --url apontando para a API em operação)"}
    try:
        r = httpx.get(url.rstrip("/") + "/disponibilidade", params={"horas": 72}, timeout=90.0)
        r.raise_for_status()
        d = r.json()
    except (httpx.HTTPError, ValueError) as erro:
        return {"disponibilidade_72h": None, "aviso": f"não foi possível ler a API ({type(erro).__name__})"}
    saude = httpx.get(url.rstrip("/") + "/saude", timeout=30.0).json()
    return {"disponibilidade_72h": d["disponibilidade_geral"], "intervalo_leitura_min": d["intervalo_leitura_min"],
            "calculado_em": d["calculado_em"], "fonte_leituras": saude.get("fonte_leituras"),
            "alimentador_demo": saude.get("alimentador_demo"),
            "aviso": ("leituras SIMULADAS do alimentador de demonstração: mede a operação do sistema, não sensores reais"
                      if saude.get("alimentador_demo") else "leituras recebidas do gateway")}


def revocacao_vermelho():
    metricas = json.loads((RAIZ / "ml" / "saida" / "metricas.json").read_text(encoding="utf-8"))
    return {"revocacao_vermelho": metricas["revocacao_vermelho"], "origem_dados": metricas["origem_dados"],
            "aviso": metricas["aviso"]}


def _pct(x):
    return "sem dados" if x is None else f"{x * 100:.1f}%".replace(".", ",")


def _situacao(valor, meta):
    return "—" if valor is None else ("atingida" if valor >= meta else "não atingida")


def relatorio_md(r):
    u, d, v = r["usabilidade"], r["disponibilidade"], r["revocacao"]
    linhas = [
        ("Social e usabilidade", "Taxa de adoção autônoma", _pct(u.get("adocao_autonoma")), "≥ 70% (mínimo de 10 participantes)",
         _situacao(u.get("adocao_autonoma"), METAS["adocao_autonoma"])),
        ("Usabilidade", "Clareza percebida (notas 4 ou 5)", _pct(u.get("clareza_4_ou_5")), "≥ 80%",
         _situacao(u.get("clareza_4_ou_5"), METAS["clareza_4_ou_5"])),
        ("Operacional", "Disponibilidade de leituras válidas (72 h)", _pct(d.get("disponibilidade_72h")), "≥ 95%",
         _situacao(d.get("disponibilidade_72h"), METAS["disponibilidade_72h"])),
        ("Confiabilidade da IA", "Revocação da classe Vermelho (teste)", _pct(v["revocacao_vermelho"]), "≥ 90%",
         _situacao(v["revocacao_vermelho"], METAS["revocacao_vermelho"])),
        ("Econômica e ambiental", "Redução do desperdício de água", "não medido", "sem meta no semestre", "plano de mensuração"),
        ("Produtiva", "Redução de perdas por identificação tardia", "não medido", "indicador de longo prazo", "futuro"),
    ]
    tabela = "\n".join(f"| {a} | {b} | {c} | {d_} | {e} |" for a, b, c, d_, e in linhas)
    avisos = [f"- Usabilidade: {u['aviso']}." for _ in [0] if u.get("aviso")]
    avisos += [f"- Disponibilidade: {d['aviso']}."] if d.get("aviso") else []
    avisos += [f"- Revocação do Vermelho: {v['aviso']}"]
    return f"""# Indicadores de impacto (calculados)

Gerado por `{r['comando']}` em {r['gerado_em']}. Planilha: `{r['planilha']}` ({u['participantes']} participantes com consentimento).

| Dimensão | Indicador | Resultado | Meta (relatório, Quadro 5) | Situação |
|---|---|---|---|---|
{tabela}

## Avisos

{chr(10).join(avisos)}
- Os indicadores de água e de perdas não têm número neste semestre (relatório, seção 9.2). Veja o plano de
  mensuração em `docs/usabilidade/analise_de_impacto.md`.
- Resultados de teste de protótipo, em ambiente controlado; não representam resultados em lavouras.
"""


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    opcoes = argparse.ArgumentParser(description="Indicadores de impacto a partir da coleta real.")
    opcoes.add_argument("--planilha", default=str(PLANILHA_PADRAO))
    opcoes.add_argument("--url", default=None, help="URL da API em operação (para a disponibilidade de 72 h)")
    opcoes.add_argument("--saida", default=str(SAIDA_PADRAO))
    args = opcoes.parse_args(argv)
    resultado = {
        "comando": "python ml/calcular_indicadores.py" + (" --url <url>" if args.url else ""),
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "planilha": Path(args.planilha).name, "metas": METAS,
        "usabilidade": adocao_e_clareza(args.planilha),
        "disponibilidade": disponibilidade(args.url),
        "revocacao": revocacao_vermelho(),
    }
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    (saida / "indicadores.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    (saida / "indicadores.md").write_text(relatorio_md(resultado), encoding="utf-8")
    print(relatorio_md(resultado))
    return 0


if __name__ == "__main__":
    sys.exit(main())
