# 🌱 AgroAnálise: Inclusão Digital no Campo com IoT e Machine Learning

Projeto Integrador IV (2026/2) — FAESA Centro Universitário — Sistemas de Informação e Ciência da Computação
Professor: Prof. M.Sc. Howard Cruz Roatti 

O **AgroAnálise** é um sistema de monitoramento de plantações de café (Arábica e Conilon) que combina Internet das Coisas (IoT), Machine Learning e uma aplicação web. Ele transforma leituras de solo e clima em um **semáforo** simples, voltado a agricultores familiares com baixo letramento digital.
 
## 📍 Status dos checkpoints
 
| Checkpoint | Prazo | Situação |
|---|---|---|
| **C1 – Relatório** | 18/09/2026 | Entregue e **revisado** conforme a correção do professor e o edital (ver `Relatorio_AgroAnalise_Projeto_Integrador_IV final.pdf` e `docs/`) |
| **C2 – Protótipo (vídeo)** | 30/10/2026 | Vídeo do protótipo no YouTube (ver `Link video`) |
| **C3 – MVP** | 04/12/2026 | Em andamento: aplicação web, testes, eval da IA, deploy com URL pública e análise de impacto |

## 📄 Documentos

- Relatório (PDF): [`Relatorio_AgroAnalise_Projeto_Integrador_IV final.pdf`](Relatorio_AgroAnalise_Projeto_Integrador_IV%20final.pdf)
- Relatório (Word, editável): [`docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx`](docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx)
- Fontes de dados e referências: [`docs/fontes.md`](docs/fontes.md)
- Registro do uso de IA (com os prompts): [`docs/uso-de-ia/REGISTRO.md`](docs/uso-de-ia/REGISTRO.md)
- Vídeo do protótipo: ver o arquivo `Link video`

## 🎯 1. Escopo e regras de negócio

* **Área temática:** Tecnologia e Inovação (recorte em inclusão digital e sustentabilidade no campo). **ODS:** 9, 12 e 8.
* **Público-alvo:** agricultores familiares com letramento digital baixo ou nulo.
* **Cultura inicial:** café (Arábica e Conilon).
* **Variáveis:** umidade do solo, temperatura do ambiente e umidade relativa do ar.
* **Entrega de valor:** aplicação web com semáforo (🟢 Ideal, 🟡 Atenção, 🔴 Ação crítica), com texto e ícone além da cor, última atualização e aviso de dados indisponíveis.
* **Fora do escopo do MVP:** acionamento automático de irrigação, diagnóstico de doenças, estimativa de produtividade, recomendação agronômica individualizada e aplicativo móvel nativo.

## 🌍 2. Comunidade impactada e indicadores

Agricultores familiares cafeicultores do Espírito Santo. Segundo o Censo Agropecuário 2017 (IBGE, conferido no SIDRA), o estado tinha 108.014 estabelecimentos agropecuários, 74,8% deles de agricultura familiar, e 78,8% dos estabelecimentos familiares não recebiam orientação técnica. A caracterização completa está na seção 9.1 do relatório.

| Indicador | Meta proposta (C3) |
|---|---|
| Taxa de adoção autônoma (3 tarefas sem ajuda) | ≥ 70% dos participantes (mínimo de 10). |
| Clareza percebida do semáforo (escala 1 a 5) | ≥ 80% das respostas 4 ou 5. |
| Disponibilidade de leituras válidas (72 h) | ≥ 95%. |
| Revocação da classe Vermelho (conjunto de teste) | ≥ 0,90. |
| Redução do desperdício de água | Plano de mensuração (sem meta numérica no semestre). |
| Redução de perdas por identificação tardia | Indicador de longo prazo. |

## ⚙️ 3. Arquitetura

1. **Aquisição:** Arduino com sensor de umidade do solo e DHT11 enviam as leituras por porta serial.
2. **Gateway local (Python):** PySerial, Pandas e NumPy validam e tratam as leituras, guardam o histórico em SQLite e enviam os dados à nuvem por HTTPS autenticado.
3. **Aplicação em nuvem:** API (backend) que armazena as leituras, executa o classificador Scikit-Learn (`.pkl`) e gera uma mensagem curta em linguagem simples (LLM via API do GroqCloud, com mensagens-padrão de contingência).
4. **Apresentação:** frontend web com o semáforo virtual.

O LLM **não decide** a classe: apenas reformula, em linguagem simples, a classificação feita pelo modelo supervisionado, a partir de entradas estruturadas.

## 🧪 4. Avaliação (eval) e testes

* **Classificador:** divisão 80/20 (estratificada quando possível), matriz de confusão, precisão, revocação, F1-Score e acurácia por classe e média macro, com linha de base e foco nos falsos negativos da classe crítica. Os dados simulados serão identificados como tais.
* **Camada de explicação (LLM):** 30 cenários avaliados quanto a coerência com a classe, ausência de recomendação agronômica específica, tamanho e linguagem, falhas da API e consumo de tokens.
* **Testes de software:** unitários, de integração e de ponta a ponta (incluindo falhas de sensor, mensagem serial incompleta e indisponibilidade do LLM).

## 🔐 5. IA responsável

LGPD (sem dados pessoais na operação básica), mitigação de *prompt injection* (entrada estruturada, sem texto livre), segredos fora do repositório, transparência sobre limitações e acompanhamento de custo (tokens e chamadas no plano gratuito).

## 📅 6. Plano de trabalho por checkpoint

* **C1:** escopo, justificativa, metodologia, comunidade, indicadores, plano de trabalho e repositório inicial.
* **C2:** montagem dos sensores, comunicação serial, banco SQLite, dataset, treino inicial do classificador, primeiros testes e vídeo.
* **C3:** aplicação web, camada de explicação, integração completa, testes, eval, deploy com URL pública, documentação e análise de impacto.

## 👥 Equipe

Cauan Henrique Damascena Gomes · Eduardo Rodrigues Rangel Malaquias · Guilherme de Souza Paiva · Juliano de Andrade Dantas Rodrigues · Rubiale Alves de Melo Filho

Cada integrante faz *commits* com o próprio usuário e e-mail. O uso de IA no desenvolvimento é registrado em `docs/uso-de-ia/`.

.
