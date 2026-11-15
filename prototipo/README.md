# AgroAnálise: protótipo navegável (C2)

Protótipo demonstrativo do semáforo de cafezais. **Todos os dados são simulados** (o Arduino ainda não está montado) e
**as faixas de Ideal/Atenção/Crítico são provisórias, não são parâmetros agronômicos validados.**

O classificador (Scikit-Learn) decide a classe; o LLM (GroqCloud) apenas reformula a mensagem. Sem chave ou com falha,
o sistema usa mensagens-padrão e o semáforo continua funcionando.

## Rodar em 5 comandos (a partir da pasta `prototipo/`)

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt
python ml/treinar.py --salvar                       # gera dataset, modelo.pkl e metricas.json
uvicorn app.principal:app                           # sobe API + páginas
# abra http://localhost:8000
```

Atalho: `python executar_demo.py` treina se faltar o modelo e sobe o servidor.

Sem `--salvar`, `ml/treinar.py` só mostra as métricas e não sobrescreve os arquivos versionados.
As faixas (limites físicos, intervalo de treino e faixas provisórias de rotulagem) ficam em `config/faixas.json`,
lido pelo gerador do dataset, pela API (`GET /faixas`) e pela interface.

## Classificador: números atuais (teste, 600 amostras simuladas)

| Configuração | Revocação do Vermelho | Precisão do Vermelho | Acurácia | F1 macro |
|---|---|---|---|---|
| Árvore sem ajuste | 0,809 | 0,893 | 0,752 | 0,740 |
| Só limiar conservador (0,15) | 0,918 | 0,792 | 0,742 | 0,707 |
| **Peso 3 para o Vermelho (modelo usado)** | **0,922** | **0,817** | **0,760** | **0,732** |
| Teto de referência: a própria regra sem ruído | 0,911 | 0,893 | 0,818 | 0,803 |
| Linha de base (classe majoritária) | 1,000 | 0,428 | 0,428 | 0,200 |

- A configuração foi escolhida por **validação cruzada (k=5) só no treino** (maior F1 macro entre as que atingem
  revocação do Vermelho ≥ 0,90); o teste foi usado uma única vez, para relatar. A meta de 0,90 foi atingida, com
  custo: mais falsos alarmes (precisão do Vermelho caiu de 0,893 para 0,817; revocação do Amarelo de 0,546 para 0,434).
- O **teto de referência** mostra que ~0,82 é o máximo esperável de acurácia: os rótulos têm ruído de medição que
  nenhum modelo recupera. A regra escrita pelo grupo, sem ML, ainda supera a árvore.
- **O ML aqui valida o pipeline, não a eficácia agronômica em campo.** Os rótulos vêm de regras sobre as mesmas
  variáveis de entrada.
- As barras de "proporção" na página de IA são a fração (ponderada pelo peso do Vermelho) de amostras de treino
  parecidas em cada classe. Não são confiança nem certeza.
- O `modelo.pkl` continua versionado até o deploy; no deploy ele será gerado no build (`python ml/treinar.py --salvar`),
  para não amarrar o binário à versão do scikit-learn.

## LLM (opcional)

Copie `.env.example` para `.env` e preencha `GROQ_API_KEY` (e, se quiser, `GROQ_MODELO`; padrão `llama-3.1-8b-instant`).
A chave nunca é gravada no código nem no repositório (`.env` está no `.gitignore`).
Sem chave, as respostas trazem `origem_mensagem: "padrao"`.

## Testes

```bash
python -m pytest -v
```

Nenhum teste usa a rede: o LLM é simulado com `monkeypatch`.

## Rotas

`GET /saude` · `GET /faixas` · `POST /classificar` (`?simular_falha_llm=true` para mostrar o fallback) · `GET /metricas` ·
`GET /cenarios` · `GET /talhoes` · `GET /simulador/leituras` (`?passo=`, `?talhao=`, `?simular_falha_llm=true`) ·
`GET /historico?talhao=A` · `GET /status` (fonte ativa) · `POST /leituras` (gateway, com token) · `GET /disponibilidade?horas=72` · `GET /riscos/regioes` · `GET /riscos/{regiao_id}`

## Páginas

| Página | O que mostra |
|---|---|
| `index.html` | Início e **modo apresentação** (botão "Iniciar demonstração" ou `index.html?demo=1`) |
| `agricultor.html` | Semáforo gigante, uma frase e o botão **Ouvir** (voz do navegador, pt-BR) |
| `talhoes.html` | 8 pontos de monitoramento ao vivo, ordenados por gravidade, com filtros |
| `painel.html` | Um talhão ao vivo (pausar, 1×/2×/4×) ou cenários prontos; barras com zonas |
| `historico.html` | 24 h simuladas de um talhão (gráfico e tabela) |
| `mapa.html` | Mapa de riscos **simulados** da região (módulo demonstrativo): camadas, orientações gerais e fonte oficial; a localização fica só no aparelho |
| `ia.html` | Formulário que chama `/classificar` de verdade, com proporções e selo da mensagem |
| `avaliacao.html` | Métricas reais, teto de referência e comparação do Vermelho |
| `sobre.html` | O que não faz, limites e IA responsável |

Alternador **Agricultor / Técnico** em todas as páginas, pela URL (`?visao=agricultor` ou `?visao=tecnico`); nada é
guardado no aparelho. Cada estado tem cor, palavra, ícone e **forma** (círculo = Ideal, triângulo = Atenção,
octógono = Ação crítica; tracejado cinza = sem dados).

## Simulador ao vivo

As leituras dos talhões vêm de uma `FonteDeLeituras` (`app/fontes.py`). Hoje a fonte ativa é a `FonteSimulada`:
determinística (mesmo passo, mesma leitura), sem estado no servidor. Cada passo vale 10 minutos simulados e o relógio
avança um passo a cada 3 s reais; a interface pausa ou acelera pedindo outro passo. O solo seca em ciclos, a
temperatura sobe à tarde, há dias com chuva simulada e um sensor (talhão H) que fica sem sinal de vez em quando.
Cada leitura passa pela mesma avaliação do `/classificar` (`app/servico.py`). A `FonteBanco` (gateway) vem na Etapa 4.
O roteiro do modo apresentação fica em `web/ativos/roteiro_demo.json` e pode ser editado sem mexer no código.

## Pipeline com banco e gateway (dados do sensor)

O caminho previsto no relatório (seções 7.3, 8.2 e 8.4) já roda de ponta a ponta, **com o Arduino simulado**:

```
Arduino (ou porta virtual) --serial--> gateway (valida, guarda em SQLite local) --HTTPS + token--> POST /leituras
   --> banco (SQLAlchemy) --> FonteBanco --> /status --> páginas
```

Para ver funcionando (dois terminais, dentro de `prototipo/`; no `.env` defina `TOKEN_DISPOSITIVO` com um valor longo):

```bash
# terminal 1: API lendo do banco; leitura com mais de 1 min vira "sem dados" (bom para demonstrar)
set FONTE_LEITURAS=banco& set MINUTOS_DESATUALIZADO=1& .venv\Scripts\python -m uvicorn app.principal:app
# terminal 2: gateway com Arduino simulado (porta virtual loop://), um ciclo a cada 5 s
.venv\Scripts\python -m gateway.gateway --simulado --api http://localhost:8000 --intervalo 5
```

Pare o gateway (Ctrl+C) e, depois de 1 minuto, as páginas mostram **Sem dados atualizados** (cinza, nunca uma cor).
Para o banco não abrir vazio: `.venv\Scripts\python -m app.semear --horas 72` (leituras simuladas).

- **Banco:** `DATABASE_URL` (padrão SQLite em `prototipo/dados/`; no deploy, Postgres gerenciado, porque o disco
  de serviços gratuitos pode ser apagado). Tabelas criadas no startup; leituras únicas por (talhão, instante).
- **Ingestão:** `POST /leituras` exige `Authorization: Bearer <TOKEN_DISPOSITIVO>`; recusa campos extras, valores
  fora do possível (contados como rejeição) e datas sem fuso, no futuro ou muito antigas; reenviar a mesma leitura
  não duplica (200), mesma chave com valores diferentes dá 409.
- **Gateway** (`gateway/`): protocolo `P:A;N:128;S:432;T:27.5;U:61` (S = leitura bruta do solo, 0..1023).
  Descarta mensagem incompleta, falha do DHT11 (`nan`), sensor de solo solto, valor fora da faixa, reenvio (mesmo N)
  e oscilação abrupta (mediana das últimas 5). Guarda tudo em SQLite local e reenvia com espera exponencial.
- **Arduino** (`arduino/agroanalise/agroanalise.ino`): **não testado em hardware**; traz o esquema de ligação.
  **A calibração do sensor de solo está pendente**: os valores 850 (seco) e 400 (molhado) são provisórios.
- **Disponibilidade** (`GET /disponibilidade`): leituras válidas recebidas ÷ esperadas (um envio por ponto a cada
  `INTERVALO_LEITURA_MIN`), meta ≥ 95% em 72 h. Descartes feitos no gateway contam como leituras que faltaram.

## Avaliação (eval) da IA

- **Classificador:** `python ml/avaliar_classificador.py` gera [`docs/avaliacao/classificador.md`](../docs/avaliacao/classificador.md)
  (validação cruzada k=5 no treino, busca de hiperparâmetros, teste usado uma vez, IC de Wilson, linha de base e
  regra de referência).
- **Camada de explicação (LLM):** `python ml/avaliar_llm.py` (mock reprodutível, sem rede) gera
  [`docs/avaliacao/llm.md`](../docs/avaliacao/llm.md): 30 cenários, filtro de saída contra respostas rotuladas e falhas
  da API pelo caminho HTTP. `python ml/avaliar_llm.py --ao-vivo` usa o Groq de verdade (precisa de `GROQ_API_KEY`)
  e gera `llm_ao_vivo.md` com colunas para revisão humana.

## Segurança e deploy

- `MODO_DEMO=1` libera a simulação de falha do LLM e `/simulador/leituras`; sem ele, ficam desligados (403).
- Limite de pedidos por IP e por minuto (429 com `Retry-After`), teto de chamadas ao Groq por minuto e por dia,
  corpo máximo de 16 KB (413), cabeçalhos de segurança (CSP, `nosniff`, `X-Frame-Options`, HSTS em https) e CORS
  só para `ORIGENS_PERMITIDAS`.
- `Dockerfile` (gera o `modelo.pkl` no build) e `render.yaml` na raiz. Passo a passo em
  [`docs/DEPLOY.md`](../docs/DEPLOY.md). Teste de fumaça: `.venv\Scripts\python scripts\teste_fumaca.py --url <url>`.

## Limites do protótipo

- Dados 100% simulados, com semente fixa; nenhuma medição real.
- Rótulos gerados por regras sobre as mesmas variáveis de entrada: as métricas validam o pipeline, não a eficácia em campo.
- Sem acionamento de irrigação, diagnóstico de doenças, recomendação agronômica ou login.
- Arduino ainda não montado: o gateway roda com porta virtual; sketch e calibração não testados em hardware.
- Sem dados pessoais.
