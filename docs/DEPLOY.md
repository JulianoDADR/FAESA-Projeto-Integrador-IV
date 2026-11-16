# Deploy do AgroAnálise na Vercel + Turso

Passo a passo para **um integrante do grupo** publicar o MVP. A IA **não** faz o deploy, o push nem cria segredos:
quem faz é o grupo, na própria conta. Depois, rode o teste de fumaça contra a URL pública e cole a saída
real no relatório.

> **Transparência:** a demonstração principal continua com `FONTE_LEITURAS=simulada`. O Turso é a persistência
> preparada para as leituras; a prova com o banco é separada e não transforma os dados simulados em dados de campo.
> Nada aqui foi publicado ainda. As regras dos planos gratuitos mudam: confira no painel da Vercel, do Turso e do
> Groq antes de começar e registre a data em `docs/fontes.md`.

## 1. O que roda onde

| Parte | Onde roda | Observação |
|---|---|---|
| API FastAPI + páginas | Função Python da Vercel | Entrypoint `prototipo/index.py`; projeto com **Root Directory `prototipo`**. |
| Modelo e métricas | Bundle da função | `modelo.pkl` e `metricas.json` **versionados**; não são treinados no build. |
| Banco | Turso/libSQL | Opcional para a demo; necessário para a prova de persistência e para leituras do gateway. |
| Gateway/Arduino | Computador local (Windows) | O gateway não roda na Vercel. O Arduino continua **não testado em hardware**. |
| LLM | GroqCloud | Só reformula a classe; sem chave, vale a mensagem-padrão. |

A Vercel executa funções serverless: **não há tarefa em segundo plano confiável**. Por isso `ALIMENTADOR_DEMO` é
ignorado quando `VERCEL` está definido e a semente deve ser feita manualmente (`SEMEAR_SE_VAZIO=0`).

## 2. Antes de começar

1. A branch com o código precisa estar no GitHub. O push é feito pelo grupo.
2. Tenha uma conta na Vercel e um banco no Turso.
3. Tenha a chave do GroqCloud (`console.groq.com`). O modelo padrão do projeto é `openai/gpt-oss-20b`.
4. No Windows, execute os testes locais com SQLite (o driver libSQL não é usado localmente):

   ```powershell
   uv venv --python 3.13 "C:\caminho\fora\do\repo\agro313"
   uv pip install --python "C:\caminho\fora\do\repo\agro313\Scripts\python.exe" -r prototipo\requirements.txt
   "C:\caminho\fora\do\repo\agro313\Scripts\python.exe" -m pytest -q
   ```

   Se não tiver `uv`, use `py -3.13 -m venv C:\caminho\fora\do\repo\agro313` e
   `...\Scripts\python.exe -m pip install -r prototipo\requirements.txt`.

5. Gere um token longo para o gateway, se for usar `POST /leituras`:
   `python -c "import secrets; print(secrets.token_urlsafe(32))"`. Guarde num gerenciador de senhas.

## 3. Turso e validação remota (GitHub Actions)

No Windows local, o desenvolvimento e os testes usam **SQLite** (o driver libSQL não é instalado/validado localmente).
A conexão real com o Turso é validada **somente** em ambiente Linux, pelo workflow manual do GitHub Actions
`.github/workflows/turso-validar-semeadura.yml` (`workflow_dispatch`). **Não considere a conexão real ao Turso
validada antes da execução remota bem-sucedida desse workflow.**

Configure no repositório (Settings → Secrets and variables → Actions) os segredos `TURSO_DATABASE_URL` e
`TURSO_AUTH_TOKEN` (nunca em código, log ou commit). O diagnóstico `prototipo/scripts/verificar_turso.py` tem quatro
modos; os três primeiros **não escrevem** no banco:

| Modo | O que faz | Falha quando |
|---|---|---|
| `--modo conexao` | `SELECT 1` e informa se `leituras`/`rejeicoes` existem | só se a conexão falhar (banco novo vazio **não** é falha) |
| `--modo estrutura` | confere tabelas, índices e a restrição única `(talhao_id, coletado_em)` | algo ausente |
| `--modo persistencia --horas N` | conta leituras na janela, por origem, e procura duplicações | 0 leituras, origem inesperada ou duplicação |
| `--modo semear --horas N --confirmar-escrita` | **escreve**: cria as tabelas inexistentes (modelo SQLAlchemy), semeia leituras **simuladas** e repete a semeadura no mesmo instante para provar que não duplica | repetição gravou algo, estrutura ou persistência inválida |

Como rodar o workflow (aba **Actions → turso-validar-semeadura → Run workflow**):

1. **Somente leitura (padrão):** deixe `executar_semente` desmarcado. O workflow confere os secrets, valida a conexão,
   informa se as tabelas existem e termina **sem modificar o banco**.
2. **Com escrita (autorização explícita):** marque `executar_semente`, escolha `horas` (24, 48 ou 72, lista fechada) e
   digite exatamente `SEMEAR` em `confirmacao_escrita`. Sem a palavra, o workflow para antes de gravar. Depois da
   semeadura, os passos de estrutura e persistência rodam em modo somente leitura.

Os inputs nunca são interpolados no shell: chegam por variável de ambiente e são validados (`case 24|48|72`). O script
imprime só o host do banco, nunca o token nem a URL completa. A semente grava `origem="simulado"`: isso prova
persistência, **não** medição de campo nem disponibilidade de 72 h.

Para a demonstração do MVP sem Arduino, mantenha `FONTE_LEITURAS=simulada`. Com `FONTE_LEITURAS=simulada`, uma falha de
banco no startup é *fail-soft*: as páginas, `/status`, `/historico`, `/talhoes`, `/classificar` e `/metricas`
continuam; as rotas que precisam do banco respondem **503**. Com `FONTE_LEITURAS=banco`, uma falha de banco no startup
é **fatal** (não exibir dado velho como atual).

## 4. Criar o projeto na Vercel

1. *Add New → Project* e importe o repositório do GitHub.
2. Em **Root Directory**, escolha **`prototipo`**.
3. Framework Preset: **FastAPI** (a Vercel detecta o `fastapi` no `requirements.txt` e o `index.py` com o objeto ASGI
   `app`; se o painel sugerir outro preset, escolha FastAPI). A versão do Python vem de `prototipo/.python-version` (3.13).
4. Não configure `buildCommand` de treino. O `modelo.pkl` e o `metricas.json` versionados entram no bundle.
5. Em **Environment Variables**, cadastre as variáveis da seção 5. Segredos (`TURSO_AUTH_TOKEN`, `GROQ_API_KEY`,
   `TOKEN_DISPOSITIVO`) ficam somente no painel da Vercel.
6. Faça o deploy. O `vercel.json` inclui `config/`, `web/`, `ml/saida/modelo.pkl`, `ml/saida/metricas.json` e
   `app/riscos/orientacoes.json` na função. `includeFiles`/`excludeFiles` são **uma string glob** (ex.:
   `"{config/**,web/**}"`), como pede a documentação da Vercel; o `.vercelignore` tira testes, bancos locais, `.env`,
   `.venv`, gateway, Arduino e scripts do upload.

O `index.py` é o entrypoint:

```python
from app.principal import app  # noqa: F401
```

Se o painel mostrar que os arquivos estáticos não entraram no bundle, confira os `includeFiles` do `vercel.json`.
O `app.mount()` das páginas pode ser promovido a CDN pela Vercel; o middleware de segurança de topo mantém as
requisições na função, mas isso precisa ser confirmado no teste de fumaça da URL real.

## 5. Variáveis de ambiente

| Variável | Demo na Vercel | Para que serve |
|---|---|---|
| `TURSO_DATABASE_URL` | URL do painel | Banco remoto. Fica no painel; não versionar. |
| `TURSO_AUTH_TOKEN` | token do painel | Segredo do Turso. **Nunca** no repositório, log ou vídeo. |
| `FONTE_LEITURAS` | `simulada` | Fonte da demo (MVP sem Arduino). Troque para `banco` só depois de validar o Turso pelo workflow remoto; nesse caso uma falha no startup é fatal. |
| `MODO_DEMO` | `1` | Libera "Simular falha do LLM" e `/simulador/leituras`. Sem ele, ficam desligados (403). |
| `SEMEAR_SE_VAZIO` | `0` | Na Vercel, faça a semente manualmente; o startup não deve tentar gravar 72 h em toda instância. |
| `ALIMENTADOR_DEMO` | `0` | Ignorado quando `VERCEL` está definido. Não há tarefa em segundo plano confiável. |
| `INTERVALO_LEITURA_MIN` | `10` | Intervalo esperado entre leituras (indicador de disponibilidade). |
| `MINUTOS_DESATUALIZADO` | `15` | Leitura mais antiga que isso vira "sem dados atualizados" (cinza). |
| `TOKEN_DISPOSITIVO` | vazio ou token gerado | Exigido em `POST /leituras`. Segredo. Vazio = recebimento desligado (503). |
| `GROQ_API_KEY` | chave do Groq | Camada de explicação. Sem ela, mensagens-padrão. Segredo. |
| `GROQ_MODELO` | `openai/gpt-oss-20b` | Modelo do Groq. |
| `GROQ_MAX_POR_MINUTO` / `GROQ_MAX_POR_DIA` | `20` / `1000` | Teto de chamadas; ao estourar, mensagem-padrão. Ajuste abaixo do console. |
| `ORIGENS_PERMITIDAS` | vazio | Só se outro site precisar chamar a API (CORS). |

Para a prova com banco na Vercel, depois de validar a conexão pelo workflow remoto do GitHub Actions, troque `FONTE_LEITURAS` para `banco`. Se o Turso
falhar nesse modo, o startup falha de propósito: não adianta mostrar uma cor velha como se fosse leitura atual.

## 6. Modelo e bundle

- O classificador usa apenas umidade do solo, temperatura e umidade do ar. O LLM não decide a classe.
- O `.pkl` foi regenerado com Python **3.13.16** e `scikit-learn==1.9.1` (as versões estão fixadas em
  `requirements.txt`). A suíte roda no GitHub Actions (Ubuntu, Python 3.13), que cobre a execução em Linux; o deploy real
  e o bundle da Vercel ainda precisam ser verificados.
- Para regerar conscientemente: `python ml/treinar.py --salvar`. Não faça isso em todo build: o dataset é
  determinístico, e o arquivo versionado preserva a rastreabilidade da avaliação.
- Limite de bundle Python da Vercel: **500 MB** descompactados (documentação da Vercel consultada em 2026-11-16).
  Estimativa feita em 2026-11-16 baixando os wheels Linux/cp313 de `requirements.txt` e somando o tamanho descompactado:
  **≈ 297 MB** (scipy ≈ 112, numpy ≈ 56, pandas ≈ 44, scikit-learn ≈ 31, sqlalchemy ≈ 18, libsql ≈ 14). É uma
  estimativa: confirme o tamanho real no log do build. `pytest` e `pyserial` somam ≈ 6 MB e ficam no
  `requirements.txt` porque a CI instala exatamente o mesmo arquivo. Nunca tire o modelo do bundle.
- A CI roda `python ml/treinar.py --conferir`: treina sem gravar e falha se alguma métrica divergir do
  `metricas.json` versionado (exceto a data). Assim o build não retreina e o modelo continua rastreável.

## 7. Demonstrar a consulta ao Turso sem trocar `FONTE_LEITURAS`

O semáforo continua na fonte **simulada** (dinâmica). A prova do banco usa rotas que leem o Turso diretamente,
qualquer que seja a fonte:

1. Rode o workflow `turso-validar-semeadura` com escrita autorizada (seção 3), por exemplo `horas=24`.
2. Abra `https://<sua-url>/saude`: deve mostrar `"fonte_leituras": "simulada"`, `"banco": "libsql"` e
   `"banco_disponivel": true`.
3. Abra `https://<sua-url>/disponibilidade?horas=24`: as contagens `validas` por talhão vêm **do Turso**. Diga no vídeo
   que são leituras **simuladas** gravadas pela semente (é prova de persistência, não de disponibilidade em campo).
4. Opcional (grava 1 leitura simulada): `python scripts/teste_fumaca.py --url https://<sua-url> --gravar` com
   `TOKEN_DISPOSITIVO` no ambiente; recarregue `/disponibilidade` e veja o talhão A subir.

Ensaio local em 2026-11-16 (SQLite no lugar do Turso, Python 3.13.16): depois de `python -m app.semear --horas 24`
(1112 leituras simuladas), `/disponibilidade?horas=24` leu o banco com `FONTE_LEITURAS=simulada` e `/saude` mostrou
`banco=sqlite`, `banco_disponivel=true`. **No Turso real esse roteiro ainda não foi executado.**

Se o Turso estiver fora do ar, `/saude` responde 200 com `banco_disponivel=false`, as páginas e o semáforo seguem
(fail-soft) e `/disponibilidade` responde 503 (verificado localmente, ver `docs/testes.md`).

## 8. Primeiro acesso e teste de fumaça

1. Abra `https://<sua-url>/saude` e confira `estado`, `modelo_carregado`, `fonte_leituras`, `banco` e
   `banco_disponivel`.
2. Abra `https://<sua-url>/index.html?demo=1`.
3. Rode, dentro de `prototipo/`:

   ```bash
   python scripts/teste_fumaca.py --url https://<sua-url>
   ```

   Ele confere `/saude`, cabeçalhos de segurança (inclusive HSTS em https), as 9 páginas, `/metricas`, `/status`,
   `/historico`, `/disponibilidade`, `/riscos/regioes`, `/riscos/{regiao_id}`, `/classificar` e a recusa de
   `/leituras` sem token. Com `--gravar` e `TOKEN_DISPOSITIVO`, envia uma leitura simulada. Sai com código 1 se
   algo falhar.

Na última execução local (http, sem `--gravar`) o resultado foi **24 de 24**. O número da URL pública só pode ser
preenchido depois do deploy real.

## 9. Gateway apontando para a URL pública

Com o Arduino simulado (ou o hardware, ainda não montado):

```bash
set TOKEN_DISPOSITIVO=<o mesmo token do servidor>
python -m gateway.gateway --simulado --api https://<sua-url> --intervalo 60
```

Antes, garanta que `ALIMENTADOR_DEMO=0` e que `FONTE_LEITURAS=banco` se quiser ver as leituras do gateway. O gateway
roda no computador local, não na Vercel.

## 10. Riscos conhecidos e limites

- **Vercel serverless:** sem tarefa em segundo plano; o alimentador é ignorado. O primeiro acesso pode ter cold start.
- **Turso/libSQL:** o driver não é usado no Windows local; a conexão real é validada pelo workflow manual do GitHub Actions (Ubuntu) e no deploy.
- **Bundle:** limite de 500 MB para Python; estimativa de ≈ 297 MB; medir o tamanho real no build.
- **Criação de tabelas no startup:** `banco.configurar()` roda `create_all` ao iniciar a função. Num Turso vazio, o
  primeiro acesso ao site cria as tabelas (só as inexistentes; nada é apagado). Para manter o banco intocado até a
  semeadura autorizada, faça o workflow **antes** de configurar o Turso na Vercel.
- **Banco:** com `FONTE_LEITURAS=banco`, indisponibilidade no startup falha de propósito. Com `simulada`, o
  fail-soft mantém a demonstração e as rotas de banco respondem 503.
- **Cota do Groq:** cache, teto por minuto/dia e limite por IP; ao estourar, mensagem-padrão.
- **Uma instância:** o limitador de pedidos fica em memória; com várias instâncias, cada uma conta a sua parte.
- **Dados:** a semente grava 72 h **simuladas**; nunca apresente como medição real.
- **Não testado/validado ainda:** deploy real na Vercel, comportamento dos estáticos/CDN e **conexão real ao Turso** (depende da execução remota do workflow `turso-validar-semeadura` com os segredos configurados).

## 11. Alternativa legada (opcional)

`render.yaml` e `Dockerfile` permanecem no repositório como alternativa opcional. Atenção: o `render.yaml` usa
`FONTE_LEITURAS=banco`, `ALIMENTADOR_DEMO=1` e `SEMEAR_SE_VAZIO=1` (servidor contínuo); **não** são os valores do C3
na Vercel. A alternativa não é exigida localmente. O caminho recomendado para o C3 é **Vercel + Turso**. Se usar a alternativa, valide com o teste de fumaça contra a URL pública.
