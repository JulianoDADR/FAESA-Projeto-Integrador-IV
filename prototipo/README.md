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
`GET /historico?talhao=A`

## Páginas

| Página | O que mostra |
|---|---|
| `index.html` | Início e **modo apresentação** (botão "Iniciar demonstração" ou `index.html?demo=1`) |
| `agricultor.html` | Semáforo gigante, uma frase e o botão **Ouvir** (voz do navegador, pt-BR) |
| `talhoes.html` | 8 pontos de monitoramento ao vivo, ordenados por gravidade, com filtros |
| `painel.html` | Um talhão ao vivo (pausar, 1×/2×/4×) ou cenários prontos; barras com zonas |
| `historico.html` | 24 h simuladas de um talhão (gráfico e tabela) |
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

## Limites do protótipo

- Dados 100% simulados, com semente fixa; nenhuma medição real.
- Rótulos gerados por regras sobre as mesmas variáveis de entrada: as métricas validam o pipeline, não a eficácia em campo.
- Sem acionamento de irrigação, diagnóstico de doenças, recomendação agronômica, login, banco em nuvem ou deploy (C3).
- Sem dados pessoais.
