# Deploy do AgroAnálise (URL pública do C3)

Passo a passo para **um integrante do grupo** publicar o MVP. O Claude Code **não** faz o deploy: quem faz é o grupo,
na própria conta. Depois, rode o teste de fumaça (seção 5) contra a URL pública e cole a saída no relatório.

O relatório (seções 6.3 e 8.4) cita Render ou Railway no plano gratuito. Este guia usa o **Render**, com o
`Dockerfile` de `prototipo/`. O mesmo `Dockerfile` serve para o Railway.

> **Confira as regras vigentes antes de começar.** Planos gratuitos mudam. Em novembro de 2026 não conferimos no
> site: (a) se o serviço gratuito "dorme" depois de um tempo sem acesso e quanto demora para acordar; (b) se o disco
> é apagado a cada reinício; (c) se o Postgres gratuito tem prazo de validade. Anote o que encontrar em
> `docs/fontes.md` (com data de acesso). O sistema foi preparado para funcionar mesmo no pior caso (veja a seção 3).

## 1. Antes de começar

1. A branch com o código precisa estar no GitHub (o push é feito pelo grupo; o Claude Code não faz push).
2. Rode localmente, dentro de `prototipo/`: `.venv\Scripts\python -m pytest -q` (tudo verde).
3. Gere um token longo para o gateway (não use o de exemplo):
   `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Guarde num gerenciador de senhas.
4. Tenha a chave do GroqCloud (console.groq.com, "API Keys"). Em **Settings → Limits** do console, anote os limites
   do plano gratuito para o modelo escolhido e ajuste `GROQ_MAX_POR_MINUTO` e `GROQ_MAX_POR_DIA` abaixo deles.
   O modelo `llama-3.1-8b-instant` estava listado como "Production" na documentação do Groq em 15/11/2026.

## 2. Criar o serviço no Render

**Opção A, blueprint (mais rápida):** no painel do Render, *New → Blueprint*, escolha o repositório. O arquivo
`render.yaml` da raiz cria o serviço `agroanalise` com o Docker de `prototipo/`, health check em `/saude` e as
variáveis da seção 3 (o `TOKEN_DISPOSITIVO` é gerado pelo Render). Ele pedirá para preencher `GROQ_API_KEY` e,
se quiser, `DATABASE_URL`.

**Opção B, manual:** *New → Web Service*, conecte o repositório e configure:

| Campo | Valor |
|---|---|
| Runtime / Language | Docker |
| Root Directory | `prototipo` |
| Dockerfile Path | `./Dockerfile` |
| Instance Type | Free |
| Health Check Path | `/saude` |

O build instala as dependências e **gera o `modelo.pkl` no próprio build** (`python ml/treinar.py --salvar`), com a
mesma versão do scikit-learn da imagem. Conferimos localmente que esse treino reproduz exatamente as métricas versionadas.

## 3. Variáveis de ambiente

| Variável | Valor recomendado na URL de avaliação | Para que serve |
|---|---|---|
| `MODO_DEMO` | `1` | Libera "Simular falha do LLM" e `/simulador/leituras`. Sem ele, ficam desligados (403). |
| `FONTE_LEITURAS` | `banco` | As páginas leem o banco (o caminho real do gateway). `simulada` usa o simulador rápido (com 1×/2×/4×). |
| `ALIMENTADOR_DEMO` | `1` | Grava uma leitura **simulada** por talhão a cada `INTERVALO_LEITURA_MIN`, pelo mesmo caminho da ingestão. **Desligue (`0`) quando um gateway real estiver enviando.** |
| `SEMEAR_SE_VAZIO` | `1` | Se o banco estiver vazio ao iniciar, grava 72 h de leituras simuladas (o deploy nunca abre vazio). |
| `INTERVALO_LEITURA_MIN` | `10` | Intervalo esperado entre leituras (indicador de disponibilidade e alimentador). |
| `MINUTOS_DESATUALIZADO` | `15` | Leitura mais antiga que isso vira "sem dados atualizados" (cinza). |
| `TOKEN_DISPOSITIVO` | o token gerado no passo 1.3 | Exigido em `POST /leituras`. **Segredo.** |
| `GROQ_API_KEY` | a chave do Groq | Camada de explicação. Sem ela, o sistema usa as mensagens-padrão. **Segredo.** |
| `GROQ_MODELO` | `llama-3.1-8b-instant` | Modelo do Groq. |
| `GROQ_MAX_POR_MINUTO` / `GROQ_MAX_POR_DIA` | `20` / `1000` (ou abaixo do limite do console) | Teto de chamadas; ao estourar, vale a mensagem-padrão. |
| `DATABASE_URL` | vazio **ou** a URL de um Postgres gerenciado | Vazio = SQLite no disco do serviço (pode ser apagado a cada reinício; a semente refaz 72 h simuladas). |
| `ORIGENS_PERMITIDAS` | vazio | Só se outro site precisar chamar a API (CORS). As páginas são servidas pela própria API. |

**Banco:** sem `DATABASE_URL` o sistema funciona, mas o histórico pode sumir em cada reinício (a semente cobre a
demonstração). Para guardar as leituras de um gateway real por mais tempo, crie um Postgres gerenciado e cole a
"Internal Database URL" em `DATABASE_URL` (o código aceita `postgres://` e `postgresql://`). **Atenção:** o pacote do
driver do Postgres (por exemplo `psycopg`) ainda **não** está no `requirements.txt`; se for usar Postgres, adicione
o driver, teste localmente e só então publique.

**Nunca** cole chaves no `render.yaml`, no README, em issues ou no vídeo.

## 4. Primeiro acesso

1. Abra `https://<sua-url>/saude`. A primeira resposta pode demorar se o serviço estava "dormindo"
   (a interface mostra "O servidor está acordando…").
2. Abra `https://<sua-url>/index.html?demo=1` para conferir o modo apresentação.

## 5. Teste de fumaça (obrigatório antes de entregar)

Dentro de `prototipo/`, com o venv:

```bash
.venv\Scripts\python scripts\teste_fumaca.py --url https://<sua-url>
```

Ele confere `/saude`, cabeçalhos de segurança (inclusive HSTS em https), as 9 páginas (incluindo `mapa.html`),
`/metricas`, `/status`, `/historico`, `/disponibilidade`, `/riscos/regioes`, `/riscos/{regiao_id}`,
`/classificar` (válido, fora de faixa e com texto livre), a recusa de `/leituras` sem token e o limite de tamanho.
Com `--gravar` (e `TOKEN_DISPOSITIVO` no ambiente) também envia uma leitura simulada. Sai com código 1 se algo
falhar. Cole a saída em `docs/testes.md`.

Na última execução local (http, sem `--gravar`), o resultado foi **24 de 24 verificações OK**. Na URL pública, com
https e `--gravar`, o total é maior (HSTS e as duas verificações de gravação); use o número da saída real.

## 6. Gateway apontando para a URL pública

Com o Arduino (ou o modo simulado), no computador do gateway:

```bash
set TOKEN_DISPOSITIVO=<o mesmo token do servidor>
.venv\Scripts\python -m gateway.gateway --simulado --api https://<sua-url> --intervalo 60
```

Antes, mude `ALIMENTADOR_DEMO` para `0` no Render, para não misturar as duas fontes.

## 7. Riscos conhecidos

- **Serviço dormindo:** o primeiro acesso pode demorar; o alimentador para enquanto o serviço dorme, e esse
  intervalo aparece como leituras que faltaram no indicador de disponibilidade.
- **Disco efêmero:** sem Postgres, o histórico pode ser apagado num reinício (a semente refaz 72 h simuladas).
- **Cota do Groq:** protegida por cache, teto de chamadas e limite de pedidos por IP; ao estourar, mensagem-padrão.
- **Uma instância só:** o limite de pedidos fica em memória; com várias instâncias, cada uma conta a sua parte.
- **Não testado nesta máquina:** a construção da imagem Docker (não havia Docker instalado) e o Postgres.
