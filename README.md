# 🌱 AgroAnálise: Inclusão Digital no Campo com IoT e Machine Learning

Projeto Integrador IV (2026/2) — FAESA Centro Universitário — Sistemas de Informação e Ciência da Computação
Professor: Prof. M.Sc. Howard Cruz Roatti

O **AgroAnálise** é um sistema de monitoramento de plantações de café (Arábica e Conilon) que combina Internet das Coisas (IoT), Machine Learning e uma aplicação web. Ele transforma leituras de solo e clima em um **semáforo** simples, voltado a agricultores familiares com baixo letramento digital.

> **Dados simulados.** O Arduino ainda não foi montado: todas as leituras do MVP são simuladas e aparecem marcadas
> como simuladas na tela, no banco e nos arquivos. As faixas de Ideal, Atenção e Crítico são **provisórias** (não são
> parâmetros agronômicos validados).

## 📍 Status dos checkpoints

| Checkpoint | Prazo | Situação |
|---|---|---|
| **C1 – Relatório** | 18/09/2026 | Entregue e **revisado** conforme a correção do professor e o edital (ver `Relatorio_AgroAnalise_Projeto_Integrador_IV final.pdf` e `docs/`) |
| **C2 – Protótipo (vídeo)** | 30/10/2026 | Vídeo do protótipo no YouTube (ver `Link video`) |
| **C3 – MVP** | 04/12/2026 (confirmar no AVA) | Aplicação web, simulador, pipeline com gateway simulado, avaliação da IA, testes com CI e preparação para **Vercel + Turso** prontos na branch `eduardo/c3`. Faltam: validação da conexão Turso pelo workflow remoto e deploy com URL pública, testes com pessoas, montagem do Arduino, vídeo (ver [`docs/DIVISAO_DE_TRABALHO.md`](docs/DIVISAO_DE_TRABALHO.md)) |

URL pública: **[a preencher depois do deploy]** · Vídeo do MVP: **[a preencher]**

## 🚀 Como rodar (5 comandos, Windows, Python 3.13)

```bash
cd prototipo
py -3.13 -m venv .venv                                  # sem o "py -3.13": uv venv --python 3.13 .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pytest -q
.venv\Scripts\python -m uvicorn app.principal:app      # abra http://localhost:8000/index.html?demo=1
```

No Windows, os testes locais usam SQLite. Variáveis opcionais em `prototipo/.env.example` (chave do Groq, Turso/libSQL,
token do gateway). O deploy recomendado usa Vercel (função Python) + Turso, com passo a passo em
[`docs/DEPLOY.md`](docs/DEPLOY.md). A suíte completa (incluindo testes do driver libSQL) e a validação da conexão Turso
rodam no GitHub Actions (Ubuntu); a conexão Turso só é considerada validada após o workflow remoto bem-sucedido. Detalhes
em [`prototipo/README.md`](prototipo/README.md).

> **Estado em 2026-11-16 (verificado localmente):** `pytest` no Windows com Python 3.13.16 = 245 aprovados, 6 pulados
> (driver libSQL, só roda na CI Ubuntu), 0 falhas; teste de fumaça local 24 de 24. **Ainda não verificado:** execução
> da CI com as mudanças desta etapa, conexão com o Turso real, deploy na Vercel, Groq real ao vivo, teste com
> participantes e disponibilidade de 72 h. Arduino **não montado**; todas as leituras são **simuladas**.

## 🗂️ Estrutura

| Pasta | Conteúdo |
|---|---|
| `prototipo/app/` | API FastAPI: validação, classificador, camada de explicação (LLM), banco, ingestão, segurança, mapa de riscos |
| `prototipo/web/` | Páginas (HTML + Tailwind + JS puro): início com modo apresentação, agricultor, talhões, painel, histórico, mapa, IA, avaliação, sobre |
| `prototipo/ml/` | Dataset simulado, treino, avaliação do classificador e do LLM, cálculo dos indicadores |
| `prototipo/gateway/` · `prototipo/arduino/` | Gateway local (serial → validação → SQLite → API) e sketch do Arduino (não testado em hardware) |
| `prototipo/testes/` | Testes automatizados (pytest), rodando no GitHub Actions |
| `docs/` | Relatório, arquitetura, avaliação, testes, deploy, IA responsável, usabilidade, fontes e registro do uso de IA |

## 📄 Documentos

- Relatório (PDF): [`Relatorio_AgroAnalise_Projeto_Integrador_IV final.pdf`](Relatorio_AgroAnalise_Projeto_Integrador_IV%20final.pdf) · (Word, editável): [`docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx`](docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx)
- Textos prontos para atualizar o relatório no C3: [`docs/ATUALIZACOES_RELATORIO_C3.md`](docs/ATUALIZACOES_RELATORIO_C3.md)
- Arquitetura: [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md) · Deploy: [`docs/DEPLOY.md`](docs/DEPLOY.md)
- Avaliação da IA: [`docs/avaliacao/classificador.md`](docs/avaliacao/classificador.md) e [`docs/avaliacao/llm.md`](docs/avaliacao/llm.md)
- Testes: [`docs/testes.md`](docs/testes.md) · IA responsável: [`docs/ia_responsavel.md`](docs/ia_responsavel.md)
- Usabilidade e impacto: [`docs/usabilidade/`](docs/usabilidade/) · Ampliação de escopo (mapa de riscos): [`docs/AMPLIACAO_DE_ESCOPO.md`](docs/AMPLIACAO_DE_ESCOPO.md)
- Roteiro do vídeo do MVP: [`docs/video_mvp_roteiro.md`](docs/video_mvp_roteiro.md) · Divisão de trabalho: [`docs/DIVISAO_DE_TRABALHO.md`](docs/DIVISAO_DE_TRABALHO.md)
- Fontes de dados e referências: [`docs/fontes.md`](docs/fontes.md)
- Registro do uso de IA (com os prompts): [`docs/uso-de-ia/REGISTRO.md`](docs/uso-de-ia/REGISTRO.md)
- Vídeo do protótipo (C2): ver o arquivo `Link video`

## 🎯 1. Escopo e regras de negócio

* **Área temática:** Tecnologia e Inovação (recorte em inclusão digital e sustentabilidade no campo). **ODS:** 9, 12 e 8.
* **Público-alvo:** agricultores familiares com letramento digital baixo ou nulo.
* **Cultura inicial:** café (Arábica e Conilon).
* **Variáveis:** umidade do solo, temperatura do ambiente e umidade relativa do ar.
* **Entrega de valor:** aplicação web com semáforo (🟢 Ideal, 🟡 Atenção, 🔴 Ação crítica), com palavra, ícone e **forma** além da cor (círculo, triângulo, octógono), última atualização e aviso de dados indisponíveis (cinza, nunca uma cor de avaliação).
* **Fora do escopo do MVP:** acionamento automático de irrigação, diagnóstico de doenças, estimativa de produtividade, recomendação agronômica individualizada e aplicativo móvel nativo.
* **Ampliação demonstrativa:** mapa de riscos da região com dados simulados e orientações gerais ([`docs/AMPLIACAO_DE_ESCOPO.md`](docs/AMPLIACAO_DE_ESCOPO.md)).

## 🌍 2. Comunidade impactada e indicadores

Agricultores familiares cafeicultores do Espírito Santo. Segundo o Censo Agropecuário 2017 (IBGE, conferido no SIDRA), o estado tinha 108.014 estabelecimentos agropecuários, 74,8% deles de agricultura familiar, e 78,8% dos estabelecimentos familiares não recebiam orientação técnica. A caracterização completa está na seção 9.1 do relatório.

| Indicador | Meta proposta (C3) | Resultado atual |
|---|---|---|
| Taxa de adoção autônoma (3 tarefas sem ajuda) | ≥ 70% dos participantes (mínimo de 10) | a medir (teste com pessoas) |
| Clareza percebida do semáforo (escala 1 a 5) | ≥ 80% das respostas 4 ou 5 | a medir (teste com pessoas) |
| Disponibilidade de leituras válidas (72 h) | ≥ 95% | a medir (URL pública em operação) |
| Revocação da classe Vermelho (conjunto de teste) | ≥ 0,90 | **0,922** (IC 95%: 0,883 a 0,949), dados simulados |
| Redução do desperdício de água | Plano de mensuração (sem meta numérica no semestre) | plano em `docs/usabilidade/analise_de_impacto.md` |
| Redução de perdas por identificação tardia | Indicador de longo prazo | futuro |

## ⚙️ 3. Arquitetura

1. **Aquisição:** Arduino com sensor de umidade do solo e DHT11 enviam as leituras por porta serial (sketch pronto, **não testado em hardware**; no MVP, Arduino simulado em porta virtual).
2. **Gateway local (Python):** PySerial, Pandas e NumPy validam e tratam as leituras, guardam o histórico em SQLite e enviam os dados à nuvem por HTTPS autenticado, com retentativa.
3. **Aplicação em nuvem:** API (FastAPI na Vercel) que armazena as leituras (SQLAlchemy, com Turso/libSQL no deploy ou SQLite local no desenvolvimento), executa o classificador Scikit-Learn e gera uma mensagem curta em linguagem simples (LLM via GroqCloud, com filtro de saída e mensagens-padrão de contingência).
4. **Apresentação:** frontend web com o semáforo virtual, visão do agricultor e visão técnica.

O LLM **não decide** a classe: apenas reformula, em linguagem simples, a classificação feita pelo modelo supervisionado, a partir de entradas estruturadas. Diagrama e decisões em [`docs/ARQUITETURA.md`](docs/ARQUITETURA.md).

## 🧪 4. Avaliação (eval) e testes

* **Classificador:** 80/20 estratificada, validação cruzada k=5 só no treino, busca de hiperparâmetros, linha de base e regra de referência; revocação do Vermelho com intervalo de confiança. Os rótulos vêm de regras sobre as mesmas variáveis: **valida o pipeline, não a eficácia agronômica em campo.**
* **Camada de explicação (LLM):** 30 cenários (coerência, ausência de recomendação, tamanho, injeção de instrução, falhas da API e tokens), com modo reprodutível e modo ao vivo.
* **Testes de software:** unitários, de integração e de ponta a ponta (falhas de sensor, mensagem serial incompleta, dado desatualizado, LLM indisponível, banco fora do ar com fail-soft), rodando no GitHub Actions com Python 3.13; tabela em [`docs/testes.md`](docs/testes.md).

## 🔐 5. IA responsável

LGPD (sem dados pessoais; localização do mapa só no aparelho), mitigação de *prompt injection* (entrada estruturada, campos extras recusados), filtro de saída do LLM, segredos fora do repositório, limite de pedidos e teto de chamadas ao LLM, transparência sobre limitações e acompanhamento de custo (tokens e chamadas). Detalhes em [`docs/ia_responsavel.md`](docs/ia_responsavel.md).

## 📅 6. Plano de trabalho por checkpoint

* **C1:** escopo, justificativa, metodologia, comunidade, indicadores, plano de trabalho e repositório inicial.
* **C2:** protótipo navegável com dados simulados, dataset, treino inicial do classificador, primeiros testes e vídeo.
* **C3:** aplicação web, camada de explicação, integração completa, testes, eval, deploy com URL pública, documentação e análise de impacto.

## 👥 Equipe

Cauan Henrique Damascena Gomes · Eduardo Rodrigues Rangel Malaquias · Guilherme de Souza Paiva · Juliano de Andrade Dantas Rodrigues · Rubiale Alves de Melo Filho

Cada integrante faz *commits* com o próprio usuário e e-mail. O uso de IA no desenvolvimento é registrado em `docs/uso-de-ia/`.
