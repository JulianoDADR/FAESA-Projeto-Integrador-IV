"""Roda o pytest de verdade e gera docs/testes.md (relatorio, secao 7.6: cenario, esperado, obtido, situacao).

Uso (dentro de prototipo/):  python scripts/relatorio_testes.py
"""
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ.parent / "docs" / "testes.md"

# Cenarios exigidos pelo relatorio (7.6) e pelo plano do C3 -> testes que os cobrem (prefixo "arquivo::teste").
CENARIOS = [
    ("Unitário", "Validação de leituras (faixa, tipo, campo ausente, espécie)", "422 e nenhuma cor",
     ["test_validacao.py::"]),
    ("Unitário", "Conversão e tratamento da linha serial (protocolo e calibração)", "valores convertidos; linha quebrada recusada",
     ["test_gateway.py::test_interpreta", "test_gateway.py::test_linhas_quebradas", "test_gateway.py::test_calibracao",
      "test_gateway.py::test_validador_converte"]),
    ("Unitário", "Fonte única das faixas (config/faixas.json)", "gerador, validação e API usam o mesmo arquivo",
     ["test_faixas.py::"]),
    ("Unitário", "Escolha da mensagem de contingência", "mensagem-padrão quando o LLM falha ou erra",
     ["test_explicacao.py::"]),
    ("Unitário", "Regra conservadora do Vermelho (limiar e peso)", "nunca tira um Vermelho; desempate documentado",
     ["test_decisao.py::"]),
    ("Integração", "API ↔ modelo ↔ camada de explicação", "classe do classificador; LLM só reformula",
     ["test_api.py::", "test_simulador.py::test_rota_simulador_usa_o_mesmo"]),
    ("Integração", "Caminho HTTP do LLM: 429, timeout, sem rede, JSON malformado, saída incoerente",
     "mensagem-padrão, semáforo segue funcionando, chave fora dos logs", ["test_llm_http.py::"]),
    ("Integração", "API ↔ banco: ingestão autenticada e idempotente", "401/503 sem token; 409 em conflito; sem duplicar",
     ["test_ingestao.py::test_token", "test_ingestao.py::test_sem_token", "test_ingestao.py::test_reenvio",
      "test_ingestao.py::test_requisicoes_malformadas"]),
    ("Ponta a ponta", "Gateway simulado → API → classificação → /status", "talhões classificados e marcados como simulados",
     ["test_gateway.py::test_ponta_a_ponta"]),
    ("Falha", "Sensor desconectado (leitura bruta no extremo do ADC)", "linha descartada com motivo",
     ["test_gateway.py::test_validador_descarta_com_motivo"]),
    ("Falha", "Mensagem serial incompleta", "linha descartada com motivo",
     ["test_gateway.py::test_linhas_quebradas", "test_gateway.py::test_validador_descarta_com_motivo"]),
    ("Falha", "Valor fora do intervalo esperado", "descartado no gateway e recusado na API (contado)",
     ["test_gateway.py::test_validador_descarta_com_motivo", "test_ingestao.py::test_valor_fora_do_possivel"]),
    ("Falha", "Ausência de dados recentes (gateway parado)", "cinza, sem cor de avaliação, com a hora da última leitura",
     ["test_ingestao.py::test_leitura_antiga", "test_ingestao.py::test_gateway_parado", "test_gateway.py::test_ponta_a_ponta"]),
    ("Falha", "LLM indisponível", "mensagem-padrão", ["test_api.py::test_llm_indisponivel", "test_llm_http.py::test_falhas_do_provedor"]),
    ("Falha", "Rede do gateway cai / API devolve 500", "leituras ficam no buffer e são reenviadas com backoff",
     ["test_gateway.py::test_falha_de_rede"]),
    ("Segurança", "Injeção de prompt (texto livre, campo extra)", "422; nada chega ao LLM",
     ["test_api.py::test_texto_livre", "test_validacao.py::test_texto_livre", "test_explicacao.py::test_entrada_do_llm",
      "test_avaliacao.py::test_avaliacao_mock"]),
    ("Segurança", "Abuso: limite por IP, corpo grande, MODO_DEMO, cabeçalhos, CORS, teto do LLM",
     "429, 413, 403 e cabeçalhos presentes", ["test_seguranca.py::"]),
    ("Interface", "Páginas, roteiro da demonstração e privacidade (sem armazenamento local)", "200; roteiro válido",
     ["test_interface.py::"]),
    ("Mapa de riscos", "Esquema do /riscos/{regiao_id}, orientações com fonte oficial e sem dose/produto/manejo, "
     "coordenada do usuário fora dos pedidos", "GeoJSON válido; nenhuma orientação proibida; só o nome da região vai à API",
     ["test_riscos.py::"]),
    ("Impacto", "Cálculo dos indicadores (adoção autônoma, clareza, disponibilidade)", "sem coleta = sem dados; regras do Quadro 5",
     ["test_indicadores.py::"]),
]


def rodar_pytest(xml):
    comando = [sys.executable, "-m", "pytest", "-q", f"--junitxml={xml}"]
    processo = subprocess.run(comando, cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return processo.returncode, processo.stdout.strip().splitlines()


def ler_resultados(xml):
    resultados = {}
    for caso in ET.parse(xml).getroot().iter("testcase"):
        arquivo = caso.get("classname", "").split(".")[-1] + ".py"
        nome = f"{arquivo}::{caso.get('name')}"
        falhou = caso.find("failure") is not None or caso.find("error") is not None
        pulou = caso.find("skipped") is not None
        resultados[nome] = "reprovado" if falhou else ("pulado" if pulou else "aprovado")
    return resultados


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    with tempfile.TemporaryDirectory() as pasta:
        xml = Path(pasta) / "resultado.xml"
        codigo, saida = rodar_pytest(xml)
        resultados = ler_resultados(xml)
    resumo = next((l for l in reversed(saida) if re.search(r"\d+ (passed|failed)", l)), "")
    total = len(resultados)
    aprovados = sum(v == "aprovado" for v in resultados.values())

    linhas = []
    for tipo, cenario, esperado, prefixos in CENARIOS:
        cobertos = [n for n in resultados if any(n.startswith(p) for p in prefixos)]
        ok = [n for n in cobertos if resultados[n] == "aprovado"]
        situacao = "aprovado" if cobertos and len(ok) == len(cobertos) else ("sem teste" if not cobertos else "reprovado")
        obtido = f"{len(ok)} de {len(cobertos)} testes passaram"
        linhas.append(f"| {tipo} | {cenario} | {esperado} | {obtido} | **{situacao}** |")

    por_arquivo = {}
    for nome, situacao in sorted(resultados.items()):
        arquivo, teste = nome.split("::", 1)
        por_arquivo.setdefault(arquivo, []).append((teste, situacao))
    lista = []
    for arquivo, testes in por_arquivo.items():
        lista.append(f"\n### `testes/{arquivo}` ({sum(s == 'aprovado' for _, s in testes)} de {len(testes)})\n")
        lista += [f"- {'✅' if s == 'aprovado' else '❌'} `{t}`" for t, s in testes]

    texto = f"""# Testes automatizados

Gerado por `python scripts/relatorio_testes.py` (dentro de `prototipo/`) em
{datetime.now(timezone.utc).isoformat(timespec="seconds")}, a partir de uma execução real do `pytest`.
O mesmo `pytest` roda no GitHub Actions a cada push (`.github/workflows/testes.yml`), sem segredos: o LLM é sempre
simulado e cada teste usa um banco SQLite temporário.

**Resultado: {aprovados} de {total} testes aprovados** (`{resumo}`).

## Cenários exigidos (relatório, seção 7.6) e o que cobre cada um

| Tipo | Cenário | Resultado esperado | Resultado obtido | Situação |
|---|---|---|---|---|
{chr(10).join(linhas)}

## O que NÃO é testado automaticamente

- O Arduino e o sensor de verdade (o sketch não foi carregado em hardware; a calibração está pendente).
- A qualidade das mensagens do Groq real (só com `python ml/avaliar_llm.py --ao-vivo` e revisão humana).
- A renderização visual das páginas e a voz do botão “Ouvir” (verificadas à mão e com o Chrome sem interface,
  fora do `pytest`; a acessibilidade foi medida com o Lighthouse).
- A imagem Docker e o deploy real (o teste de fumaça `scripts/teste_fumaca.py` roda contra a URL pública).

## Lista completa
{chr(10).join(lista)}
"""
    SAIDA.write_text(texto, encoding="utf-8")
    print(f"{aprovados} de {total} aprovados · {resumo}")
    print(f"Relatório em {SAIDA}")
    return codigo


if __name__ == "__main__":
    sys.exit(main())
