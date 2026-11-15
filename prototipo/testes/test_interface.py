"""Verificacoes estaticas da interface: roteiro da demonstracao, regras de privacidade e paginas servidas."""
import json
import re
from pathlib import Path

import pytest

from app.fontes import TALHOES
from app.validacao import validar_leitura

WEB = Path(__file__).resolve().parent.parent / "web"
PAGINAS = sorted(p.name for p in WEB.glob("*.html"))
TIPOS_DE_PASSO = {"abertura", "cenario", "sem_dados", "talhoes", "mapa", "agricultor", "fim"}


def test_roteiro_da_demonstracao_e_valido():
    roteiro = json.loads((WEB / "ativos" / "roteiro_demo.json").read_text(encoding="utf-8"))
    passos = roteiro["passos"]
    assert passos[0]["tipo"] == "abertura" and passos[-1]["tipo"] == "fim"
    for passo in passos:
        assert passo["tipo"] in TIPOS_DE_PASSO, passo
        assert passo["titulo"] and passo.get("duracao_s", 8) > 0
        if passo["tipo"] == "cenario":
            validar_leitura(passo["leitura"])  # leitura do roteiro precisa passar na mesma validacao da API
        if passo["tipo"] == "agricultor":
            assert passo.get("talhao", "A") in {t["id"] for t in TALHOES}
    # O roteiro cobre o que o vídeo precisa mostrar
    tipos = {p["tipo"] for p in passos}
    assert {"cenario", "sem_dados", "talhoes", "agricultor"} <= tipos
    assert any(p.get("simular_falha_llm") for p in passos)


@pytest.mark.parametrize("arquivo", sorted(WEB.rglob("*.html")) + sorted(WEB.rglob("*.js")), ids=lambda p: p.name)
def test_sem_armazenamento_local(arquivo):
    # Ignora comentarios de linha (o comum.js cita o nome justamente para dizer que nao usa).
    texto = re.sub(r"(?m)^\s*//.*$", "", arquivo.read_text(encoding="utf-8"))
    assert not re.search(r"\b(localStorage|sessionStorage|indexedDB)\b", texto)


@pytest.mark.parametrize("pagina", PAGINAS)
def test_toda_pagina_tem_comum_js_icone_e_idioma(pagina):
    html = (WEB / pagina).read_text(encoding="utf-8")
    assert '<html lang="pt-BR">' in html
    assert 'src="ativos/comum.js"' in html  # comum.js desenha a faixa DADOS SIMULADOS e o menu
    assert 'rel="icon"' in html and html.count('src="ativos/comum.js"') == 1


def test_menu_aponta_para_paginas_que_existem():
    comum = (WEB / "ativos" / "comum.js").read_text(encoding="utf-8")
    bloco = comum[comum.index("const PAGINAS"):comum.index("];")]
    for arquivo in re.findall(r'"([a-z_]+\.html)"', bloco):
        assert (WEB / arquivo).exists(), arquivo
    assert "DADOS SIMULADOS · MODO DEMONSTRAÇÃO" in comum


@pytest.mark.parametrize("pagina", PAGINAS)
def test_paginas_e_ativos_sao_servidos(cliente, pagina):
    assert cliente.get("/" + pagina).status_code == 200


def test_ativos_novos_sao_servidos(cliente):
    for ativo in ("comum.js", "barra_zonas.js", "simulador.js", "apresentacao.js", "roteiro_demo.json", "icone.svg", "estilo.css"):
        assert cliente.get("/ativos/" + ativo).status_code == 200, ativo
