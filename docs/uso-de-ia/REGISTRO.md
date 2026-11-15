# Registro do uso de IA no desenvolvimento

Conforme a seção 11 do edital do Projeto Integrador IV, todo o processo de engenharia de software feito com apoio de IA é registrado aqui, com o prompt utilizado. Quem usa a IA faz o registro no mesmo commit do material gerado ou revisado.

## Modelo de registro

```markdown
## Registro de uso de IA — AAAA-MM-DD
- **Integrante:** Nome (usuário Git)
- **Ferramenta / modelo:**
- **Tarefa:**
- **Prompt utilizado:**
  > (colar o prompt completo)
- **Resultado (resumo):**
- **O que foi aproveitado / alterado:**
- **Como foi validado:**
- **Arquivos/commit relacionados:**
```

---

## Registro de uso de IA — 2026-11-04 (1/8): conferência do relatório C1 com o edital
- **Integrante:** Juliano Dantas (JulianoDADR)
- **Ferramenta / modelo:** Claude Code (Claude Sonnet 5.5)
- **Tarefa:** comparar o relatório do projeto com o edital do PI-IV e apontar lacunas para o C1.
- **Prompt utilizado:**
  > De acordo com o edital, meu relatório está correto da C1?
  > (anexos: o edital em PDF e o relatório em PDF)
- **Resultado (resumo):** lista de pontos conformes e de lacunas: componente de IA sem LLM, deploy e plataforma web não previstos, comunidade sem caracterização, área temática e ODS ausentes, falta de registro do uso de IA, commits de apenas 3 integrantes, marcador de merge no README e erros de numeração e sumário.
- **O que foi aproveitado / alterado:** todos os pontos viraram itens de correção do relatório e do repositório.
- **Como foi validado:** histórico de commits conferido diretamente no GitHub; revisão do grupo pendente.
- **Arquivos/commit relacionados:** relatório revisado em `docs/`.

## Registro de uso de IA — 2026-11-04 (2/8): redação dos textos complementares
- **Integrante:** Juliano Dantas (JulianoDADR)
- **Ferramenta / modelo:** Claude Code (Claude Sonnet 5.5)
- **Tarefa:** redigir os textos que faltavam: enquadramento e ODS, componente de IA, arquitetura de implantação, comunidade com dados oficiais, indicadores com metas, registro de uso de IA.
- **Prompt utilizado:**
  > Sim por favor
  > (resposta à oferta de redigir os textos complementares do relatório)
- **Resultado (resumo):** textos em português para as seções 1.1, 5.7, 6.4, 7.7, 8.4, 9.1 e 9.2, com pendências sinalizadas.
- **O que foi aproveitado / alterado:** textos incorporados ao relatório. As metas dos indicadores são propostas e devem ser ajustadas pelo grupo.
- **Como foi validado:** números da comunidade conferidos nos documentos de origem (apresentação da SEAG-ES e artigo da Revista Ifes Ciência). Conferência no SIDRA/IBGE e revisão do grupo: pendentes.
- **Arquivos/commit relacionados:** `docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx`, `docs/fontes.md`.

## Registro de uso de IA — 2026-11-04 (3/8): montagem do relatório revisado e organização do repositório
- **Integrante:** Juliano Dantas (JulianoDADR)
- **Ferramenta / modelo:** Claude Code (Claude Sonnet 5.5)
- **Tarefa:** reconstruir o relatório em Word com as correções, gerar o PDF e organizar o repositório (README, fontes e registro de IA).
- **Prompt utilizado:**
  > Minha conta tá logada aqui no GitHub Desktop, também tenho acesso aos documentos do trabalho. Faça toda a C1
- **Resultado (resumo):** relatório em .docx e .pdf com numeração e sumário corrigidos; README sem o marcador de merge; pasta `docs/` com fontes e este registro.
- **O que foi aproveitado / alterado:** a ser conferido pelo grupo antes da entrega. Pendências marcadas em amarelo no relatório: recorte regional dos testes, participantes reais ou simulados e responsabilidades por integrante.
- **Como foi validado:** conferência visual do PDF gerado; revisão do grupo pendente.
- **Arquivos/commit relacionados:** commit que adiciona este registro.

## Registro de uso de IA — 2026-11-04 (4/8): troca do LLM da camada de explicação
- **Integrante:** Juliano Dantas (JulianoDADR)
- **Ferramenta / modelo:** Claude Code (Claude Sonnet 5.5)
- **Tarefa:** trocar o LLM previsto na camada de explicação (de Groq para Claude, da Anthropic) no relatório e no README, e ajustar os trechos de custo.
- **Prompt utilizado:**
  > LLM coloca "Claude" e você consegue dar o commit e publicar sem ter o símbolo da Claude?
- **Resultado (resumo):** seções 5.7, 6.4 e 10.4, Quadro 1 e referências atualizados; o texto passa a tratar o custo por uso (limite de gasto, cache, resposta curta e módulo isolado para trocar de provedor).
- **O que foi aproveitado / alterado:** relatório e README regenerados. O grupo deve confirmar que o custo da API é viável para o MVP.
- **Como foi validado:** conferência do texto extraído do PDF; revisão do grupo pendente.
- **Arquivos/commit relacionados:** `docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx`, `README.md`.

## Registro de uso de IA — 2026-11-04 (5/8): preenchimento das responsabilidades por integrante
- **Integrante:** Juliano Dantas (JulianoDADR)
- **Ferramenta / modelo:** Claude Code (Claude Sonnet 5.5)
- **Tarefa:** preencher o Quadro 7 (responsabilidades por integrante em C1, C2 e C3) do relatório.
- **Prompt utilizado:**
  > Pode preencher da maneira que você acha melhor o Cauan, Guilherme e eu participo da C2 e C1 agora os demais pode ir preenchendo da maneira mais adequada
- **Resultado (resumo):** C1 e C2 atribuídos a Cauan, Guilherme e Juliano; C3 distribuído entre os cinco integrantes.
- **O que foi aproveitado / alterado:** a divisão foi proposta pela IA e deve ser conferida e ajustada pelo grupo.
- **Como foi validado:** revisão do grupo pendente.
- **Arquivos/commit relacionados:** `docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx`.

## Registro de uso de IA — 2026-11-04 (6/8): revisão final (QA) e publicação
- **Integrante:** Juliano Dantas (JulianoDADR)
- **Ferramenta / modelo:** Claude Code (Claude Sonnet 5.5)
- **Tarefa:** revisar o relatório e o repositório como QA e como professor da disciplina, corrigir o que fosse encontrado e publicar.
- **Prompt utilizado:**
  > Show pode commitar para eu publicar, como um QA e Professor de Projeto Integrador valide tudo e publique
- **Resultado (resumo):** conferência contra o edital e a rubrica do C1; citações ligadas às referências (IBGE, Anthropic, Nações Unidas); referência do IBGE reordenada; trecho de armazenamento ajustado ao deploy em nuvem; afirmações sobre o Conilon alinhadas ao artigo citado; recorte regional (Norte e Noroeste) e perfil dos participantes dos testes definidos; vídeo do protótipo confirmado como público.
- **O que foi aproveitado / alterado:** relatório (.docx e .pdf) regenerado. O recorte regional e o perfil dos participantes foram escolhidos pela IA e devem ser confirmados pelo grupo.
- **Como foi validado:** checagens automáticas no texto do PDF (marcas soltas, citações e referências, ordem alfabética, sumário) e conferência do link do vídeo; revisão do grupo pendente.
- **Arquivos/commit relacionados:** `docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx`, `Relatorio_AgroAnalise_Projeto_Integrador_IV final.pdf`.

## Registro de uso de IA — 2026-11-04 (7/8): LLM da camada de explicação volta a ser o Groq
- **Integrante:** Juliano Dantas (JulianoDADR)
- **Ferramenta / modelo usada no desenvolvimento:** Claude Code (Claude Sonnet 5.5). O Groq (GroqCloud) é o LLM previsto **dentro do produto**, na camada de explicação; ainda não foi usado para gerar este material.
- **Tarefa:** trocar o provedor do LLM do produto de Claude para Groq no relatório e no README, por ser a opção recomendada e gratuita do edital.
- **Prompt utilizado (trecho referente à tarefa):**
  > Então vamos fazer com o Groq.
- **Resultado (resumo):** seções 5.7, 6.4 e 10.4, Quadro 1 e referências atualizados para o GroqCloud (plano gratuito), com cache, respostas curtas e mensagens-padrão de contingência.
- **O que foi aproveitado / alterado:** relatório (.docx e .pdf) e README regenerados.
- **Como foi validado:** conferência do texto extraído do PDF (menções, citações e ordem das referências); revisão do grupo pendente.
- **Arquivos/commit relacionados:** `docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx`, `README.md`.

## Registro de uso de IA — 2026-11-04 (8/8): conferência dos números da comunidade no IBGE
- **Integrante:** Juliano Dantas (JulianoDADR)
- **Ferramenta / modelo:** Claude Code (Claude Sonnet 5.5)
- **Tarefa:** conferir no IBGE os números da caracterização da comunidade e passar o relatório a citar o IBGE como fonte primária.
- **Prompt utilizado (trecho referente à tarefa):**
  > 3. Confira
- **Resultado (resumo):** consulta à API de dados abertos do IBGE (SIDRA, tabelas 6778, 6780, 6882, 6887 e 6955, UF 32). Confirmados 108.014 e 80.775 estabelecimentos, 17.088 com orientação técnica, 213.557 de 357.258 pessoas ocupadas, 1.079.038 de 3.246.763 hectares e a participação da agricultura familiar na produção de café (Conilon 51,0%; Arábica 57,6%). O número de 63.976 estabelecimentos com café e os 78,23% de familiares continuam citados ao artigo da Revista Ifes Ciência; os dados do IBGE por espécie são consistentes com ele.
- **O que foi aproveitado / alterado:** seção 9.1 reescrita com os valores do IBGE; referência da SEAG-ES removida; README e `docs/fontes.md` atualizados.
- **Como foi validado:** valores obtidos diretamente do IBGE e percentuais calculados a partir deles; revisão do grupo pendente.
- **Arquivos/commit relacionados:** `docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx`, `docs/fontes.md`, `README.md`.

## Registro de uso de IA — 2026-11-06: protótipo navegável do C2 (AgroAnálise)
- **Integrante:** Eduardo (Eduardo Rodrigues R Malaquias)
- **Ferramenta / modelo:** Claude Code (Claude Sonnet 5.5)
- **Tarefa:** construir o protótipo demonstrativo do C2 em `prototipo/`: dados simulados, classificador Scikit-Learn, API FastAPI com camada de explicação (GroqCloud com mensagens-padrão), páginas HTML navegáveis e testes automatizados.
- **Prompt utilizado:**
  > Prompt completo versionado em `PROTOTIPO.md` (raiz do repositório). Resumo fiel: construir hoje, até as 23:59, o protótipo do AgroAnálise com dados 100% simulados; API FastAPI que carrega o `.pkl` e serve páginas HTML + Tailwind (CDN) + JavaScript puro; LLM (GroqCloud) só reformula a classe calculada pelo classificador, com entrada estruturada, validação da saída e mensagem-padrão em caso de falha; faixas provisórias declaradas como não validadas; métricas honestas (linha de base, matriz de confusão, revocação do Vermelho); código em português; commits pequenos com a identidade Git do autor; sem push; sem segredos.
- **Resultado (resumo):** `prototipo/` com `ml/` (dataset simulado, treino, métricas), `app/` (API, validação, explicação), `web/` (6 páginas), `testes/` (32 testes, todos passando) e README.
- **O que foi aproveitado / alterado:** tudo foi gerado pela IA e deve ser revisado pelo autor. As faixas de rotulagem são provisórias, escolhidas pela IA só para demonstração, e não são parâmetros agronômicos. A amostragem do dataset foi reequilibrada após a primeira rodada (a classe Verde saiu com 4% das amostras). O cenário "Calor excessivo" usa umidade do ar 65% porque o modelo, com 45%, classifica como Amarelo um caso que a regra rotularia como crítico. Ideias visuais (paleta de status e semáforo com texto e ícone) vieram do projeto do hackathon, sem copiar marca ou texto.
- **Como foi validado:** `pytest -v` (32 passed); teste de fumaça com o servidor no ar (todas as páginas e rotas responderam 200, erros de validação devolveram 422 sem classe, falha simulada do LLM devolveu mensagem-padrão). A chamada real ao Groq **não foi testada** (sem chave nesta sessão).
- **Arquivos/commit relacionados:** `prototipo/`, `.gitignore`, `docs/uso-de-ia/REGISTRO.md`. Commits de `ml/` e `app/` com `testes/` vieram antes desta entrada; esta entrada fecha o conjunto.

## Registro de uso de IA — 2026-11-15: plano do C3, Etapas 0 e 1 (preparação e correções essenciais)
- **Integrante:** Eduardo (Eduardo Rodrigues R Malaquias)
- **Ferramenta / modelo:** Claude Code (Claude Opus 5.5)
- **Tarefa:** Etapa 0 (branch `eduardo/c3`, venv, testes, leitura do relatório, `CLAUDE.md`) e Etapa 1 (correções do protótipo: servidor travado pelo LLM, "probabilidades" que não são confiança, aviso de entrada fora do treino com `config/faixas.json`, revocação do Vermelho, teto de referência da acurácia e higiene do treino).
- **Prompt utilizado:**
  > Prompt completo versionado em `docs/uso-de-ia/prompts/2026-11-15_plano_c3.md`. Resumo fiel: plano em 11 etapas até o C3 (04/12/2026), com regras de ouro (honestidade, escopo do C1, código em português, commits pequenos com a identidade do Eduardo, sem push/merge/deploy, registro de IA, sem segredos, verificação real); começar pela Etapa 0 e seguir para a Etapa 1.
- **Resultado (resumo):** `pytest` de 32 para 45 testes, todos passando. Rota `/classificar` deixa de travar o servidor (chamada ao LLM no pool de threads; teste de concorrência falha no código antigo e passa no novo). `config/faixas.json` virou a fonte única das faixas (gerador, validação, `GET /faixas` e controles da `ia.html`); a API devolve `aviso_fora_da_faixa_de_treino`. Campo `probabilidades` renomeado para `proporcoes`, com explicação. Peso do Vermelho e limiar conservador comparados por validação cruzada só no treino; escolhido peso 3 sem limiar. No teste: revocação do Vermelho 0,809 → 0,922, precisão do Vermelho 0,893 → 0,817, acurácia 0,752 → 0,760, F1 macro 0,740 → 0,732. Teto de referência (regra sem ruído): acurácia 0,818. `treinar.py` só grava com `--salvar`.
- **O que foi aproveitado / alterado:** tudo gerado pela IA e revisado na sessão. Decisões tomadas pela IA, a confirmar pelo grupo: (1) manter a rota `async` e usar `run_in_threadpool`, para preservar as mensagens de erro em português na leitura manual do JSON; (2) não calibrar as proporções (só renomear e explicar); (3) critério de escolha "maior F1 macro entre as combinações com revocação ≥ 0,90"; (4) profundidade da árvore mantida em 8 (a busca de hiperparâmetros fica para a Etapa 6); (5) `modelo.pkl` continua versionado até o deploy; (6) `PROTOTIPO.md`, citado no registro do C2 mas nunca commitado, passou a ser versionado. Achado durante o trabalho: o limiar 0,5 não é neutro (desempata folhas 50/50 a favor do Vermelho); "sem limiar" passou a ser `None`.
- **Como foi validado:** `pytest -v` (45 passed); `python ml/treinar.py` sem `--salvar` não alterou arquivos; o dataset gerado a partir do JSON é idêntico ao anterior; a árvore "sem ajuste" reproduz exatamente as métricas antigas (0,809); teste de fumaça com o servidor no ar (todas as páginas e rotas responderam 200, entrada inválida devolveu 422, entrada a 50 °C devolveu o aviso); `node --check` nos scripts das páginas e execução da tabela nova da `avaliacao.html` com o `metricas.json` real. **Não testado:** a renderização das páginas em navegador (sem navegador nesta sessão) e a chamada real ao Groq (sem chave).
- **Arquivos/commit relacionados:** `CLAUDE.md`, `.gitignore`, `PROTOTIPO.md`, `prototipo/config/faixas.json`, `prototipo/app/` (`principal.py`, `faixas.py`, `decisao.py`, `classificador.py`, `validacao.py`), `prototipo/ml/` (`treinar.py`, `gerar_dataset.py`, `saida/`), `prototipo/web/` (`ia.html`, `avaliacao.html`), `prototipo/testes/`, `prototipo/README.md`, `prototipo/executar_demo.py`. Commits da branch `eduardo/c3`, de `9d46630` até o commit desta entrada.

## Registro de uso de IA — 2026-11-15: plano do C3, Etapa 2 (interface para a demonstração)
- **Integrante:** Eduardo (Eduardo Rodrigues R Malaquias)
- **Ferramenta / modelo:** Claude Code (Claude Opus 5.5)
- **Tarefa:** Etapa 2 do plano do C3: simulador ao vivo, talhões, visão do agricultor com "Ouvir", modo apresentação, barras com zonas e estados de falha amigáveis.
- **Prompt utilizado:**
  > "prossiga" (continuação do plano versionado em `docs/uso-de-ia/prompts/2026-11-15_plano_c3.md`, seção 4 / Etapa 2).
- **Resultado (resumo):** `app/fontes.py` (`FonteDeLeituras` e `FonteSimulada` determinística, 8 talhões de uma propriedade fictícia, ciclo do dia, chuva simulada, sensor instável); `app/servico.py` (mesma avaliação para `/classificar` e para o simulador); rotas `/talhoes`, `/simulador/leituras` e `/historico?talhao=`. Páginas novas `talhoes.html` e `agricultor.html`; `painel.html` com modo ao vivo (pausar, 1×/2×/4×) e cenários; modo apresentação em `index.html` com roteiro em `web/ativos/roteiro_demo.json`. Formas por estado (círculo, triângulo, octógono), alternador Agricultor/Técnico por `?visao=`, `aria-live`, skeleton e aviso de "servidor acordando". `pytest`: 87 testes passando.
- **O que foi aproveitado / alterado:** gerado pela IA e revisado na sessão. Decisões da IA, a confirmar pelo grupo: polling a cada 3 s em vez de SSE (mais simples e resistente a cold start); simulador sem estado no servidor (o cliente avança o "passo"); parâmetros dos talhões e do clima são ilustrativos (calibrados só para a demo ter uma mistura realista de estados: ~16% Vermelho, ~43% Amarelo, ~40% Verde, poucos "sem dados"); ordem de gravidade Vermelho > Amarelo > Sem dados > Verde; voz do "Ouvir" prefere voz instalada no aparelho, e o `sobre.html` avisa que vozes online podem enviar o texto ao fabricante do navegador. Achados corrigidos durante a sessão: um script de edição duplicou a `historico.html` (detectado pelo teste no navegador); um marcador da barra cobria o valor. Divergência explicada na tela: a barra de uma variável pode dizer "quente" enquanto o semáforo diz "Ideal", porque a cor vem do classificador (que erra perto das fronteiras) e não da regra.
- **Como foi validado:** `pytest -v` (87 passed); navegação real no Chrome sem interface (puppeteer-core 25.16.0) em 11 URLs a 412 px: 0 erros de console ou de rede e nenhuma rolagem horizontal; modo apresentação percorreu os 9 passos sozinho (64 s até o resumo), com teclado, pausa e avanço rápido verificados; Lighthouse 13.6.0 no celular: acessibilidade 100 e boas práticas 100 em `agricultor.html`, `painel.html`, `talhoes.html` e `index.html` (o Lighthouse cobre só parte das regras de acessibilidade; não substitui teste com pessoas). **Não testado:** o som do botão "Ouvir" (o Chrome sem interface não reproduz áudio) e leitores de tela reais.
- **Arquivos/commit relacionados:** `prototipo/app/` (`fontes.py`, `servico.py`, `principal.py`), `prototipo/web/` (todas as páginas e `ativos/`), `prototipo/testes/` (`test_simulador.py`, `test_interface.py`), `prototipo/README.md`. Commits de `48fa6bb` até o commit desta entrada.

## Registro de uso de IA — 2026-11-15: plano do C3, Etapa 4 (banco, ingestão, gateway e Arduino)
- **Integrante:** Eduardo (Eduardo Rodrigues R Malaquias)
- **Ferramenta / modelo:** Claude Code (Claude Opus 5.5)
- **Tarefa:** Etapa 4 do plano do C3, feita antes da Etapa 3 (mapa) por decisão do Eduardo, por valer mais na nota: persistência, ingestão autenticada, regra de dado desatualizado, indicador de disponibilidade, gateway com modo simulado e sketch do Arduino.
- **Prompt utilizado:**
  > "melhor garantir a etapa 4 e fazer a etapa 3 depois ja que ela vale mais nota" (continuação do plano em `docs/uso-de-ia/prompts/2026-11-15_plano_c3.md`, seção 6 / Etapa 4).
- **Resultado (resumo):** `app/banco.py` (SQLAlchemy 2.1.6, `DATABASE_URL`, tabelas criadas no startup); `app/ingestao.py` e `POST /leituras` (token de dispositivo, campos extras recusados, faixa, fuso obrigatório, idempotência por talhão e instante, 409 em conflito); `FonteBanco` com `MINUTOS_DESATUALIZADO`; rota genérica `/status` pela fonte ativa (`FONTE_LEITURAS`); `/disponibilidade` (válidas ÷ esperadas, meta 95% em 72 h); `app/semear.py`; `gateway/` (protocolo, validação, buffer SQLite, envio com backoff, Arduino simulado em `loop://` do PySerial 3.5); `arduino/agroanalise/agroanalise.ino`. `pytest`: 144 testes passando.
- **O que foi aproveitado / alterado:** gerado pela IA e revisado na sessão. Decisões da IA, a confirmar pelo grupo: gateway e sketch ficam dentro de `prototipo/` (um único venv e uma única suíte de testes); a espécie vem do cadastro do talhão, não do dispositivo; valores fora do possível são recusados pela API e contados como rejeição; disponibilidade = válidas ÷ esperadas (o que o gateway descarta aparece como leitura que faltou); calibração provisória do solo (850 seco, 400 molhado); oscilação abrupta descartada até se confirmar em 3 leituras seguidas (achado durante a sessão: sem isso, uma mudança real, como uma chuva forte, seria descartada para sempre); SQLAlchemy 2.1.6 em vez da 2.1.8 por a mais nova ter menos de duas semanas.
- **Como foi validado:** `pytest -v` (144 passed), incluindo um teste de ponta a ponta (Arduino simulado → serial virtual → gateway → API → `/status` → cinza depois de o gateway parar). Execução real com processos separados: servidor com `FONTE_LEITURAS=banco` e `MINUTOS_DESATUALIZADO=1`; gateway simulado em 6 ciclos validou 44 leituras, descartou 4 (3 falhas do DHT11 e 1 sensor solto, injetadas) e enviou as 44 (HTTP 201); `/status` passou de 8 talhões sem dados para 8 classificados com origem "simulado"; páginas abertas no Chrome sem erros; 1 minuto depois de parar o gateway, os 8 talhões ficaram "Sem dados atualizados" (captura de tela conferida). Nova navegação com a fonte simulada: 0 erros em 11 páginas e o modo apresentação completo. **Não testado:** o sketch do Arduino (não foi compilado nem carregado; sem hardware e sem arduino-cli nesta máquina), a calibração do sensor e o Postgres (só SQLite foi usado).
- **Arquivos/commit relacionados:** `prototipo/app/` (`banco.py`, `ingestao.py`, `indicadores.py`, `semear.py`, `fontes.py`, `servico.py`, `principal.py`), `prototipo/gateway/`, `prototipo/arduino/`, `prototipo/web/`, `prototipo/testes/` (`test_ingestao.py`, `test_gateway.py`, `conftest.py`), `prototipo/requirements.txt`, `prototipo/.env.example`, `prototipo/.gitignore`, `prototipo/README.md`, `CLAUDE.md`. Commits de `07edd88` até o commit desta entrada.
