# CLAUDE.md — AgroAnálise (Projeto Integrador IV, FAESA)

## Visão
Monitoramento de cafezais (Arábica e Conilon) para agricultores familiares com baixo letramento digital.
Um classificador Scikit-Learn transforma **umidade do solo, temperatura e umidade do ar** em um semáforo
(Verde = Ideal, Amarelo = Atenção, Vermelho = Ação crítica). Um LLM (GroqCloud) **só reformula** em linguagem
simples a classe já calculada: **o LLM nunca decide a classe**. O relatório (C1) está em
`docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx` (não editar; textos novos vão para `docs/`).

## Comandos (rodar dentro de `prototipo/`)
```bash
py -3.13 -m venv .venv && .venv/Scripts/python -m pip install -r requirements.txt   # instalar (Windows, Python 3.13)
.venv/Scripts/python ml/treinar.py --salvar        # treinar e gravar modelo.pkl, metricas.json e dataset
.venv/Scripts/python ml/treinar.py --conferir      # não grava; falha se divergir do metricas.json (a CI roda isto)
.venv/Scripts/python -m uvicorn app.principal:app  # subir API + páginas em http://localhost:8000
.venv/Scripts/python -m pytest -v                  # testes (o LLM é sempre mockado; nenhum teste usa a rede)
.venv/Scripts/python -m gateway.gateway --simulado --api http://localhost:8000   # gateway com Arduino simulado
.venv/Scripts/python -m app.semear --horas 72      # leituras simuladas no banco (TURSO_DATABASE_URL/DATABASE_URL)
.venv/Scripts/python ml/avaliar_classificador.py   # docs/avaliacao/classificador.md
.venv/Scripts/python ml/avaliar_llm.py             # docs/avaliacao/llm.md (mock; --ao-vivo usa o Groq)
.venv/Scripts/python scripts/relatorio_testes.py   # pytest real + docs/testes.md
.venv/Scripts/python scripts/teste_fumaca.py --url <url>   # contra o servidor no ar
python scripts/verificar_turso.py --modo conexao|estrutura|persistencia   # Turso, só leitura (roda na CI Linux)
.venv/Scripts/python ml/calcular_indicadores.py    # indicadores do Quadro 5 (docs/usabilidade/)
```
Python 3.13 (`.python-version`). Variáveis: `FONTE_LEITURAS` (simulada|banco), `TOKEN_DISPOSITIVO`,
`TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`, `DATABASE_URL`, `VERCEL`, `MINUTOS_DESATUALIZADO`,
`INTERVALO_LEITURA_MIN`. Os testes usam um SQLite temporário por teste (`testes/conftest.py`).
O deploy recomendado é Vercel (`prototipo/index.py` + `vercel.json`) + Turso. No Windows local, testes usam SQLite;
a suíte completa (incluindo driver libSQL) roda no GitHub Actions (Ubuntu) e a conexão Turso é validada pelo workflow
manual remoto. Drivers libSQL têm marcador `sys_platform != "win32"`.
Sem `--salvar`, `treinar.py` só imprime as métricas (não sobrescreve arquivos versionados).

## Estrutura
- `prototipo/config/faixas.json`: fonte única das faixas (treino, rotulagem provisória, limites da interface).
- `prototipo/ml/`: geração do dataset simulado e treino/avaliação. `prototipo/app/`: API FastAPI.
- `prototipo/web/`: páginas HTML + Tailwind (CDN) + JS puro, servidas pela própria API.
- `prototipo/app/fontes.py`: `FonteDeLeituras` (simulada ou banco); `app/servico.py`: avaliação única de uma leitura.
- `prototipo/gateway/`: gateway local (serial, validação, buffer SQLite, envio). `prototipo/arduino/`: sketch (não testado).
- `prototipo/testes/`: pytest. `docs/`: fontes, registro de uso de IA e documentação.

## Convenções
- Código em **português do Brasil**: variáveis, funções, classes, rotas, campos JSON, comentários, mensagens e commits.
  Identificadores **sem acento**; textos de interface **com acento**. Nomes de bibliotecas ficam como são.
- Commits pequenos, em português, com prefixos `feat:`, `fix:`, `test:`, `docs:`, `chore:`. Cada integrante commita
  com o próprio usuário. Não fazer push, merge nem deploy sem pedido explícito.
- Sem `localStorage`/`sessionStorage` no front. Estado de visão por parâmetro de URL (`?visao=`).

## Registro do uso de IA (exigência do edital)
Toda sessão com IA ganha uma entrada em `docs/uso-de-ia/REGISTRO.md` (só o oficial de `docs/`), no formato do
modelo do próprio arquivo (integrante, ferramenta, tarefa, prompt, resultado, aproveitado/alterado, validação,
commits), **no mesmo commit** do código gerado.

## Regras de ouro
- **Honestidade:** dados simulados sempre rotulados como simulados (tela, banco, arquivos). Nunca inventar métricas,
  resultados de usuários, fontes, links ou parâmetros agronômicos. Relatar o número real, mesmo ruim.
- As faixas de classificação são **provisórias** (não validadas agronomicamente). Os rótulos vêm de regras sobre as
  mesmas variáveis de entrada: **o ML valida o pipeline, não a eficácia agronômica em campo.**
- O classificador usa só as 3 variáveis. Riscos do mapa não são feature do modelo.
- **Segredos** só por variável de ambiente (`GROQ_API_KEY`, `GROQ_MODELO`, `TOKEN_DISPOSITIVO`, `DATABASE_URL`,
  `TURSO_DATABASE_URL`, `TURSO_AUTH_TOKEN`, `MODO_DEMO`, `ORIGENS_PERMITIDAS`); nunca em código, log, commit ou README.
- **LGPD:** sem dados pessoais na operação básica. Coordenadas do usuário nunca saem do navegador.
- Verificação real: não afirmar que algo funciona sem ter rodado.

## Fora do escopo
Acionar irrigação; diagnosticar doenças ou pragas; estimar produtividade; recomendação agronômica individualizada
(produto, dose, volume, calendário); aplicativo nativo; múltiplas propriedades; orientações de prevenção geradas por
LLM; prometer economia de água, ganho de produtividade ou eficácia em campo. O mapa de riscos é módulo
**demonstrativo** (ver `docs/AMPLIACAO_DE_ESCOPO.md`). Não alterar o projeto do hackathon (VIVA+).
