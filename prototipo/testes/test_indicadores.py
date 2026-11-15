"""Etapa 8: calculo dos indicadores de impacto. Os participantes abaixo sao FICTICIOS e existem so neste teste."""
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ml"))
import calcular_indicadores as ci  # noqa: E402

CABECALHO = ("codigo,data,consentiu,perfil,dispositivo,tarefa1_ok,tarefa1_ajuda,tarefa2_ok,tarefa2_ajuda,"
             "tarefa3_ok,tarefa3_ajuda,tempo_total_s,extra_e1_ok,extra_e2_ok,clareza_1a5,observacoes")


def _planilha(tmp_path, linhas):
    caminho = tmp_path / "coleta.csv"
    caminho.write_text("\n".join([CABECALHO, *linhas]) + "\n", encoding="utf-8")
    return caminho


def test_planilha_vazia_nao_inventa_numero(tmp_path):
    r = ci.adocao_e_clareza(_planilha(tmp_path, []))
    assert r["participantes"] == 0 and r["adocao_autonoma"] is None and r["clareza_4_ou_5"] is None


def test_regras_de_autonomia_ajuda_tempo_e_consentimento(tmp_path):
    linhas = [
        "P01,2026-11-20,sim,baixo_letramento,celular,sim,nao,sim,nao,sim,nao,120,sim,sim,5,",   # autonomo
        "P02,2026-11-20,sim,produtor,celular,sim,nao,sim,sim,sim,nao,150,,,4,",                  # pediu ajuda na 2
        "P03,2026-11-20,sim,outro,celular,sim,nao,sim,nao,sim,nao,320,sim,nao,3,",              # passou de 5 min
        "P04,2026-11-20,sim,tecnico,celular,sim,nao,sim,nao,nao,nao,90,,,2,",                    # errou a 3
        "P05,2026-11-20,nao,outro,celular,sim,nao,sim,nao,sim,nao,60,,,5,",                      # sem consentimento: fora
    ]
    r = ci.adocao_e_clareza(_planilha(tmp_path, linhas))
    assert r["participantes"] == 4 and r["autonomos"] == 1 and r["adocao_autonoma"] == 0.25
    assert r["clareza_4_ou_5"] == 0.5 and r["clareza_media"] == 3.5
    assert r["minimo_atingido"] is False and "pelo menos 10" in r["aviso"]
    assert r["por_tarefa"]["tarefa2"]["precisaram_de_ajuda"] == 1
    assert r["extra_e1_ok"] == {"respostas": 2, "concluiram": 2}


def test_disponibilidade_sem_url_nao_e_medida():
    assert ci.disponibilidade(None)["disponibilidade_72h"] is None


def test_disponibilidade_le_a_api_e_avisa_quando_e_simulada(monkeypatch):
    def get_falso(url, params=None, timeout=None):
        corpo = ({"disponibilidade_geral": 0.97, "intervalo_leitura_min": 10, "calculado_em": "x"}
                 if url.endswith("/disponibilidade") else {"fonte_leituras": "banco", "alimentador_demo": True})
        return httpx.Response(200, json=corpo, request=httpx.Request("GET", url))
    monkeypatch.setattr(ci.httpx, "get", get_falso)
    d = ci.disponibilidade("https://exemplo.invalido")
    assert d["disponibilidade_72h"] == 0.97 and "SIMULADAS" in d["aviso"]


def test_relatorio_marca_meta_e_nunca_inventa_agua_e_perdas(tmp_path):
    r = {"comando": "x", "gerado_em": "x", "planilha": "x", "metas": ci.METAS,
         "usabilidade": ci.adocao_e_clareza(_planilha(tmp_path, [])), "disponibilidade": ci.disponibilidade(None),
         "revocacao": ci.revocacao_vermelho()}
    texto = ci.relatorio_md(r)
    assert "sem dados" in texto and "não medido" in texto and "plano de mensuração" in texto
