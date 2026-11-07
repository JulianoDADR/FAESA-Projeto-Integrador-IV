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
