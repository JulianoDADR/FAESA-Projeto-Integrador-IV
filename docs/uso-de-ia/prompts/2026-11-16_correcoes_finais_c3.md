# Prompt das correções finais do C3 (Eduardo, 2026-11-16)

Prompt enviado ao Claude Code (Claude Opus 5.5) na sessão de 2026-11-16, na íntegra. Antes dele, na mesma sessão,
foi pedido para criar o `prototipo/.env` local com as credenciais do Turso; as credenciais **não** são reproduzidas
aqui (ficam só no `.env`, que está no `.gitignore`).

```text
AgroAnálise C3 — Correções finais antes do GitHub, Turso e Vercel

Analise o repositório completo e siga as regras do CLAUDE.md.

Foi realizada uma auditoria independente da versão atual do AgroAnálise. A aplicação passou em 218 testes automatizados,
com 1 teste ignorado e 1 aviso, e já implementa FastAPI, SQLite, Turso/libSQL, classificador Scikit-Learn, GroqCloud,
frontend, simulador e fail-soft.

Objetivo: concluir as pendências reais de implementação, preparar a validação remota e atualizar a documentação sem
alterar desnecessariamente o código existente.

Não implemente suporte a Arduino físico nesta etapa. O MVP será demonstrado com dados simulados.

Tarefa 1 — Corrigir o workflow do Turso
Arquivos: .github/workflows/turso-validar-semeadura.yml; prototipo/scripts/verificar_turso.py; prototipo/app/banco.py,
somente se necessário.
Problema identificado: o workflow executa o diagnóstico que exige as tabelas leituras e rejeicoes antes da semeadura.
Um banco Turso novo e vazio pode falhar antes de ser inicializado.
Implementar três modos de verificação:
Conexão: somente SELECT 1, sem criar tabelas e sem fazer gravações.
Estrutura: verificar a existência das tabelas e índices necessários.
Persistência: consultar os registros após a semeadura e confirmar quantidade, origem e ausência de duplicações.
Com executar_semente=false, o workflow deve validar a conexão, informar se existem tabelas e terminar sem modificar o
banco. A ausência de tabelas não deve ser confundida com falha de conexão.
Com executar_semente=true, após validar a conexão, deve criar as tabelas inexistentes utilizando o modelo SQLAlchemy
existente, executar a semeadura, verificar a estrutura e comprovar os registros persistidos.
Repetir a semeadura na mesma janela temporal e confirmar que não gera duplicações. Preservar a UniqueConstraint
existente.

Tarefa 2 — Proteger o parâmetro de semeadura
O valor inputs.horas é utilizado diretamente no comando shell do workflow.
Substituir por uma configuração segura, preferencialmente um input do tipo choice com opções 24, 48 e 72 horas, ou
validar rigorosamente um valor inteiro antes de executar o script.
Não interpolar diretamente texto não validado no shell.
O workflow deve exigir autorização explícita para qualquer operação de escrita no Turso.

Tarefa 3 — Garantir que a CI realmente teste libSQL
Arquivo: prototipo/testes/test_driver_libsql.py.
No Windows, manter o skip explícito, pois o driver remoto é Linux/macOS.
No Ubuntu do GitHub Actions, a ausência de libsql_experimental ou sqlalchemy_libsql deve causar falha de teste, não
skip.
Testar efetivamente: Importação do driver. Carregamento do dialeto sqlite+libsql. Criação de tabelas. Inserção de um
registro. Consulta do registro. Reabertura da conexão e leitura. Tratamento de erro.
Não usar o banco Turso real nessa suíte automática.
Verificar também se o GitHub Actions está instalando exatamente as dependências de requirements.txt com Python 3.13.

Tarefa 4 — Revisar a configuração da Vercel
Arquivos: prototipo/index.py; prototipo/vercel.json; prototipo/.vercelignore; prototipo/.python-version;
prototipo/requirements.txt
Confirmar: Python 3.13. FastAPI exportado corretamente. Root Directory = prototipo. Inclusão de páginas HTML,
JavaScript, CSS, configurações, modelo e métricas. Exclusão de testes, bancos locais, .env, .venv e arquivos
desnecessários. Compatibilidade das bibliotecas e tamanho do bundle. Ausência de dependência de tarefas contínuas em
segundo plano.
Não alterar a arquitetura para Next.js.
Não reexecutar o treinamento em todos os builds. Preservar o modelo versionado e as métricas correspondentes.

Tarefa 5 — Preservar a operação sem Arduino
Manter: FONTE_LEITURAS=simulada. SEMEAR_SE_VAZIO=0. ALIMENTADOR_DEMO=0. Fonte simulada dinâmica para o semáforo. Turso
como banco persistente para a prova de integração. Fail-soft para demonstrar o site mesmo quando o banco estiver
indisponível. Não apresentar dados simulados como reais.
Criar ou revisar um procedimento documentado para demonstrar a consulta ao Turso sem precisar alterar permanentemente
FONTE_LEITURAS.

Tarefa 6 — Revisar segurança
Verificar: .gitignore da raiz e de prototipo. Ausência de credenciais, tokens e arquivos .env no Git. Nenhuma
credencial nos logs e documentação. Autenticação de POST /leituras. Respostas HTTP 401, 422, 429 e 503. Comportamento
de /saude quando o Turso falha. Compatibilidade das variáveis de ambiente com a Vercel.
Não incluir nenhuma credencial real nos testes.

Tarefa 7 — Revalidar a IA
Confirmar que: O classificador continua sendo o único responsável pelas classes Verde, Amarelo e Vermelho. O Groq
apenas reformula a mensagem. O modelo configurado é openai/gpt-oss-20b, caso continue disponível no provedor. O
fallback mantém a aplicação funcionando sem Groq. O filtro bloqueia recomendações agronômicas específicas.
Revisar a limitação documentada na avaliação do LLM: uma resposta incoerente com Verde passou pelo filtro. Se for
possível melhorar o filtro sem prejudicar mensagens legítimas, implemente testes adicionais independentes. Caso
contrário, preserve a limitação na documentação.
Não inventar resultados de avaliações ao vivo.

Tarefa 8 — Corrigir o ambiente e a rastreabilidade
A pasta .venv do ZIP ainda contém Python 3.14.6, embora a produção esteja definida para Python 3.13.
Recomendar ou executar, se possível, a recriação do ambiente local com Python 3.13 no Windows.
Não instalar Linux, WSL2 ou Docker no computador.
Revisar as alterações de finais de linha CRLF e executar: git status --short; git diff --check; git diff --stat
Evitar alterações de formatação desnecessárias.

Tarefa 9 — Atualizar documentação acadêmica
Atualizar conforme resultados efetivamente executados: docs/testes.md; docs/DEPLOY.md; docs/video_mvp_roteiro.md;
docs/usabilidade/indicadores.md, apenas quando houver novos dados; README.md; prototipo/README.md;
docs/uso-de-ia/REGISTRO.md
O roteiro ainda menciona 215 testes, mas a suíte atual possui 218 aprovados e 1 ignorado. Deixar a contagem final
vinculada à execução real da CI.
Deixar explícito: Arduino não montado. Leituras simuladas. Turso ainda depende de verificação remota. Groq real ainda
depende de teste. Usabilidade com participantes pendente. Disponibilidade de 72 horas ainda não comprovada.
Não alterar o relatório original C1 sem solicitação.

Tarefa 10 — Validação final e entrega do diagnóstico
Executar os testes possíveis localmente e informar: Resultado completo do pytest. Resultado do teste de fumaça local.
Resultados do treinamento e das avaliações simuladas. Arquivos modificados. Estado do Git. Situação da CI, Turso e
Vercel. Problemas ainda não solucionados. Comandos e ações que precisarei executar nas plataformas.

Restrições: não fazer commit, push, merge nem deploy sem minha autorização explícita. Não executar a semeadura no Turso
real sem autorização.

Primeiro conclua a implementação local e apresente um relatório técnico verificável.
```
