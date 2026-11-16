# PROMPT PARA O CLAUDE CODE: Protótipo navegável do AgroAnálise (C2)

> Como usar: abra o Claude Code na pasta do repositório do AgroAnálise (clone de https://github.com/JulianoDADR/FAESA-Projeto-Integrador-IV) e cole tudo abaixo da linha. Antes, troque o marcador `"C:\Users\CVCV-INOVACAO-BI\Desktop\hackfaesa-fase1\hackfaesa"` pelo caminho real do projeto do hackathon (VIVA+) no seu computador.

---

## 0. Contexto e prazo

Você vai me ajudar a construir, **hoje, com prazo final às 23:59 (horário de Brasília)**, o protótipo demonstrativo do projeto **AgroAnálise** (Projeto Integrador IV, FAESA, checkpoint C2). O protótipo será usado para gravar um vídeo de apresentação no YouTube. Eu sou o Eduardo e este trabalho é em grupo, mas **eu faço este protótipo sozinho agora**.

O que é o AgroAnálise: sistema de monitoramento de cafezais (Arábica e Conilon) para agricultores familiares com baixo letramento digital. Lê umidade do solo, temperatura e umidade relativa do ar, classifica em um **semáforo** (Verde = Ideal, Amarelo = Atenção, Vermelho = Ação crítica) com um classificador Scikit-Learn e gera uma mensagem curta em linguagem simples com um LLM. **O LLM nunca decide a classe: só reformula a classe calculada pelo classificador.** O relatório completo está em `docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx` (leia as seções 5.5, 6.2, 6.3, 6.4, 7.4, 7.5, 8.3, 8.4 e 10 antes de codar).

O que o C2 avalia (nota do grupo): funcionamento do componente de IA (40%), viabilidade técnica (30%), testes/eval iniciais e vídeo (30%). Portanto o protótipo precisa mostrar **IA funcionando de verdade**, métricas reais e testes automatizados rodando, não só telas bonitas.

O Arduino **não está montado**. Todo dado é **simulado** e deve ser identificado como simulado na interface, no dataset e nos arquivos (regra do relatório, seção 7.2 e 8.4 "modo demonstração").

## 1. Passo 0: analise o projeto do hackathon (somente leitura)

O projeto do hackathon (VIVA+) está em: `"C:\Users\CVCV-INOVACAO-BI\Desktop\hackfaesa-fase1\hackfaesa"`. **Não altere nada nele.** Leia-o e me entregue, **antes de escrever código**, um resumo de no máximo 15 linhas com:

1. O que existe e é reaproveitável: componentes (por exemplo `MetricCard`, `StatusBadge`, `AlertBanner`, `DataChart`), `theme.js` (tokens de cor), hooks, padrão de integração com LLM (incluindo o **modo roteiro de reserva** quando a API falha), e o guia de estilo em português (`guia-estilo-pt-br-js-ts`, se existir no projeto ou em notas).
2. O que **não** deve ser trazido: agente proativo, fila de aprovação e qualquer coisa de acionamento automático (o AgroAnálise **não** aciona irrigação, ver seção 6.3 do relatório).
3. Sua recomendação de como reaproveitar (copiar o visual/ideia para HTML, não migrar a stack Next.js para cá). Se algo do hackathon não existir ou não for reaproveitável, diga claramente e siga sem ele. **Não invente que existe.**

Depois do resumo, **siga em frente sem esperar aprovação** (o prazo é curto), a menos que encontre um bloqueio real.

## 2. Decisões já tomadas (não reabra)

- **Arquitetura "opção 2":** mini API Python (**FastAPI**) que carrega o classificador `.pkl` do Scikit-Learn e também **serve as páginas HTML estáticas**. Um único comando sobe tudo (`uvicorn`), para eu mostrar o servidor subindo na gravação.
- **Front-end:** várias páginas **HTML + Tailwind via CDN + JavaScript puro**, sem build e sem Next.js. As páginas se **navegam entre si** por um menu comum. Uma delas é a **página dinâmica e funcional da IA**, que chama a API de verdade.
- **LLM da camada de explicação:** **GroqCloud** (API compatível com OpenAI, plano gratuito), como diz o relatório. Chave só por variável de ambiente `GROQ_API_KEY`; nome do modelo por `GROQ_MODELO` (confira na documentação do Groq um modelo aberto gratuito atual, não presuma um nome antigo). Chamada isolada em um único módulo para ser trocável. **Se a chave não existir ou a API falhar, usar mensagens-padrão por classe** e informar isso na resposta (`origem_mensagem: "padrao"`).
- **Sintaxe do código em português:** nomes de variáveis, funções, classes, arquivos, rotas, campos JSON, comentários, mensagens e commits em **português do Brasil** (sem acentos em identificadores, com acentos em textos de interface). Siga o guia de estilo do hackathon se existir. Nomes obrigatórios de bibliotecas/APIs externas ficam como são.
- **Dados:** 100% simulados, com seed fixa, rotulados `origem = "simulado"`.

## 3. Estrutura a criar (dentro do repositório do AgroAnálise)

```
prototipo/
  README.md                  # como rodar, em 5 comandos, e limites do protótipo
  requirements.txt
  .env.example               # GROQ_API_KEY=, GROQ_MODELO=  (sem valores reais)
  ml/
    gerar_dataset.py         # gera ml/saida/dataset_simulado.csv
    treinar.py               # treina, avalia e salva modelo + métricas
    saida/                   # dataset_simulado.csv, modelo.pkl, metricas.json
  app/
    principal.py             # FastAPI: rotas + servir ../web
    classificador.py         # carrega modelo.pkl e classifica
    explicacao.py            # camada LLM (Groq) + mensagens-padrão + cache
    validacao.py             # validação de faixas e entrada
  web/
    index.html               # início + navegação + aviso de dados simulados
    painel.html              # semáforo navegável por cenários (3 estados + sem dados)
    historico.html           # histórico simulado (tabela + gráfico simples)
    ia.html                  # PÁGINA DINÂMICA: chama a API de verdade
    avaliacao.html           # métricas reais lidas de /metricas
    sobre.html               # limites, IA responsável, LGPD, o que NÃO faz
    ativos/                  # css/js comuns
  testes/
    test_api.py
    test_explicacao.py
    test_validacao.py
```

Não crie nada fora de `prototipo/`, exceto a entrada no registro de IA (seção 7) e, se necessário, o `.gitignore` do repositório.

## 4. Requisitos funcionais

### 4.1 Dataset e classificador (`ml/`)

- `gerar_dataset.py`: gera ~3000 amostras simuladas com `numpy` (seed fixa), colunas: `especie` (Arabica/Conilon), `umidade_solo` (%), `temperatura` (°C), `umidade_ar` (%), `classe`, `origem="simulado"`.
- **Rotulagem por regras documentadas em comentário no próprio arquivo**, com faixas **provisórias de demonstração**. Deixe explícito no código, no README e na página `sobre.html` que **as faixas NÃO são parâmetros agronômicos validados** (o relatório, seção 8.3, exige validação posterior com referências/ZARC/Embrapa). Use faixas diferentes para Arábica e Conilon só como ilustração. Adicione **ruído e sobreposição perto das fronteiras** para que o problema não seja trivial.
- `treinar.py`: divisão **80/20 estratificada**; **linha de base** (`DummyClassifier` com a classe majoritária); classificador **interpretável** (árvore de decisão ou floresta pequena; escolha e justifique em 2 linhas); métricas por classe (precisão, revocação, F1) + média macro + acurácia; **matriz de confusão**; destaque para a **revocação da classe Vermelho** (falsos negativos críticos, ver seção 7.4 do relatório). Salve `modelo.pkl` e `metricas.json` (incluindo a matriz de confusão, a linha de base, o tamanho dos conjuntos, a versão do scikit-learn e a data).
- **Seja honesto com os números:** não ajuste o problema para dar 100%. Relate o que sair. Inclua em `metricas.json` e na página de avaliação o aviso: _"Rótulos gerados por regras sobre as mesmas variáveis de entrada: este resultado valida o pipeline, não a eficácia agronômica em campo"_ (seção 5.5 do relatório).

### 4.2 API (`app/`)

- `GET /saude` → estado do serviço e se o LLM está configurado.
- `POST /classificar` com `{especie, umidade_solo, temperatura, umidade_ar}` → `{classe, rotulo, probabilidades, mensagem, origem_mensagem ("llm"|"padrao"), modo_demonstracao: true, atualizado_em}`.
- `GET /metricas` → conteúdo de `metricas.json`.
- `GET /cenarios` → lista de cenários prontos para a demo (solo seco, ideal, calor excessivo, etc.), cada um com valores simulados.
- **Validação** (`validacao.py`): rejeitar valores fora de faixa fisicamente plausível, campos ausentes e espécie desconhecida, com erro 422 e mensagem em português simples. Uma leitura inválida **nunca** gera cor de semáforo.
- **Camada de explicação** (`explicacao.py`):
  - Entrada **somente estruturada** (classe, valores numéricos validados, espécie). **Nenhum texto livre do usuário chega ao LLM** (mitigação de prompt injection).
  - Prompt: no máximo 2 frases, linguagem simples, **proíbe recomendação agronômica específica** (produtos, doses, volumes de irrigação), lembra que a decisão de manejo é do produtor.
  - Validar a saída (tamanho, idioma, coerência básica com a classe: a mensagem de Verde não pode sugerir problema, a de Vermelho não pode sugerir tranquilidade; rejeitar se tiver números de dose/volume). Se falhar, usar a mensagem-padrão.
  - Timeout curto (≈5 s), cache em memória por classe + faixa de valores, mensagens-padrão por classe.
  - Parâmetro para **forçar falha do LLM** (por exemplo `?simular_falha_llm=true`) para eu demonstrar o fallback no vídeo.
  - Registrar (log) chamadas e tokens usados, sem logar a chave.

### 4.3 Páginas (`web/`)

Menu comum em todas as páginas e **faixa fixa visível "DADOS SIMULADOS, MODO DEMONSTRAÇÃO"**. Todas funcionam bem no celular (mobile first), com contraste alto e texto grande.

- **`index.html`:** o que é o AgroAnálise, para quem é, fluxo em 4 camadas (sensores → gateway → API/IA → semáforo) e botões para as demais páginas. Diga claramente que o hardware ainda não está conectado nesta versão.
- **`painel.html`:** semáforo grande, com **texto e ícone além da cor** ("Ideal", "Atenção", "Ação crítica"), mensagem curta, **horário da última atualização**, e um seletor de cenários (Solo seco, Ideal, Calor excessivo, **Sem dados**). O estado **"Sem dados atualizados"** deve ser **cinza, sem cor de avaliação** e com aviso (regra da seção 6.2). Pode usar os cenários de `/cenarios` e a mensagem da API.
- **`historico.html`:** tabela e gráfico simples (Chart.js via CDN ou SVG próprio) de leituras simuladas das últimas horas, com a classe de cada ponto.
- **`ia.html` (a página dinâmica):** formulário (espécie + 3 controles deslizantes/campos) → `POST /classificar` → mostra classe, **probabilidades por classe**, a mensagem e um selo **"Mensagem gerada por: LLM (Groq)" ou "Mensagem-padrão (LLM indisponível)"**. Botão **"Simular falha do LLM"** e botões de cenários prontos. Mostrar erros de validação em linguagem simples. Se a API estiver fora do ar, a página mostra um aviso claro, não quebra.
- **`avaliacao.html`:** lê `/metricas` e exibe **matriz de confusão**, precisão/revocação/F1 por classe, média macro, acurácia, linha de base e o **destaque da revocação do Vermelho**, mais o aviso metodológico da seção 4.1.
- **`sobre.html`:** o que o sistema faz e **não faz** (sem acionamento de irrigação, sem diagnóstico de doenças, sem recomendação agronômica individualizada, sem app nativo), IA responsável (LGPD: sem dados pessoais; prompt injection; limites do plano gratuito; custo em tokens), e que as faixas são provisórias.

Design: simples, limpo, cores do semáforo apenas para o status (nunca decorativas), fonte legível, botões grandes. Reaproveite a identidade/ideias visuais do hackathon só se fizer sentido e **sem copiar marca ou textos do VIVA+**.

## 5. Testes (C2 pede "primeiros testes")

Use `pytest`. Mínimo de testes que realmente rodem e passem:

1. `/classificar` com entrada válida devolve uma das 3 classes e `modo_demonstracao = true`.
2. Entrada fora de faixa ou campo ausente → 422 e **nenhuma classe** devolvida.
3. LLM indisponível (simule falha com mock/monkeypatch) → resposta ainda válida com `origem_mensagem = "padrao"`.
4. Saída do LLM incoerente com a classe ou com dose/volume → cai na mensagem-padrão.
5. Entrada para o LLM contém apenas campos estruturados (teste que texto livre não é aceito).
6. `/metricas` devolve a matriz de confusão e a revocação do Vermelho.
   Rode `pytest -v` ao final e **cole a saída real** no seu relatório final. Não declare "passou" sem ter executado.

## 6. Ordem de execução e tempo (você deve me avisar se algo não couber)

Cada fase termina com **commit pequeno** (seção 7). Se o tempo apertar, **corte nesta ordem**: `historico.html` → gráfico da página de avaliação → cache do LLM → testes 4 e 5. **Nunca corte**: modelo treinado + métricas, `/classificar`, página `ia.html`, fallback do LLM, `painel.html` e pelo menos 3 testes passando.

1. **Fase 0 (≈10 min):** análise do hackathon + resumo (seção 1).
2. **Fase 1 (≈15 min):** `ml/` completo, rodar `python ml/treinar.py`, conferir `metricas.json`.
3. **Fase 2 (≈20 min):** API + validação + explicação (Groq + fallback) + testes iniciais.
4. **Fase 3 (≈25 min):** páginas HTML na ordem: `ia.html`, `painel.html`, `avaliacao.html`, `index.html`, `sobre.html`, `historico.html`.
5. **Fase 4 (≈10 min):** `pytest -v`, README, registro de IA, teste de fumaça de ponta a ponta (subir o servidor e chamar cada rota/página).
6. **Fase 5 (se sobrar tempo):** polimento visual e script `executar_demo` (um comando que treina se faltar o modelo e sobe o servidor).

## 7. Regras de repositório e de IA (obrigatórias pelo edital)

- **Commits com a minha identidade Git.** Antes do primeiro commit, rode `git config user.name` e `git config user.email` e me mostre. **Não altere a configuração.** Se não parecer ser a minha (Eduardo Rodrigues Rangel Malaquias), pare e me avise. Faça **commits pequenos ao longo do trabalho** (um por fase), com mensagens em português no estilo do repositório (`feat:`, `docs:`, `test:`). **Não faça push** sem eu pedir.
- **Registro do uso de IA:** o edital (seção 11) exige registrar o prompt usado. Ao final, adicione uma entrada em `docs/uso-de-ia/REGISTRO.md`, seguindo o **modelo que já existe nesse arquivo** (integrante: Eduardo; ferramenta: Claude Code; tarefa; prompt utilizado; resultado; o que foi aproveitado/alterado; como foi validado; arquivos/commits), **no mesmo commit** do código gerado. Cole neste registro o texto deste prompt (ou um resumo fiel e a indicação do arquivo).
- **Segredos:** nunca grave chave de API no código, em commit, em log ou em README. Crie/atualize `.gitignore` para `.env`, `__pycache__/`, `.venv/`. O `.env.example` só tem nomes de variáveis.
- **Sem dados pessoais** em lugar nenhum.

## 8. O que NÃO fazer

- Não alterar o projeto do hackathon.
- Não inventar parâmetros agronômicos como se fossem validados; não prometer economia de água, ganho de produtividade ou eficácia em campo.
- Não adicionar acionamento de irrigação, agentes proativos, login, banco em nuvem nem deploy (isso é do C3).
- Não usar `localStorage`/`sessionStorage`.
- Não instalar dependências além do necessário (sugestão: `fastapi`, `uvicorn`, `scikit-learn`, `pandas`, `numpy`, `joblib`, `httpx` ou `openai`, `pytest`, `python-dotenv`). Fixe versões no `requirements.txt` com as que você realmente instalou.
- Não dizer que algo funciona sem ter rodado.

## 9. Critérios de aceite (confira tudo antes de encerrar)

- [ ] `pip install -r requirements.txt` → `python ml/treinar.py` → `uvicorn app.principal:app` sobe sem erro e `http://localhost:8000` abre o `index.html`.
- [ ] Todas as páginas navegam entre si pelo menu; faixa "DADOS SIMULADOS" aparece em todas.
- [ ] `ia.html` classifica de verdade via API e mostra o selo de origem da mensagem; botão de falha do LLM mostra o fallback.
- [ ] `painel.html` mostra os 3 estados com texto + ícone + cor e o estado "Sem dados" em cinza.
- [ ] `avaliacao.html` mostra métricas reais (matriz de confusão, revocação do Vermelho, linha de base) com o aviso metodológico.
- [ ] `pytest -v` roda e passa; saída colada no relatório final.
- [ ] Commits com a minha identidade; registro de IA atualizado; nenhuma chave no repositório.

## 10. Relatório final (formato)

Ao terminar, responda em português, curto: (1) o que foi feito e o que foi cortado por tempo, (2) comandos exatos para rodar, (3) saída real do `pytest -v` e as métricas principais (acurácia, revocação do Vermelho, linha de base), (4) o que **eu** preciso fazer ainda (por exemplo configurar a `GROQ_API_KEY`, conferir a identidade Git, fazer push), (5) riscos e limitações conhecidos.

Comece pelo Passo 0 agora.
