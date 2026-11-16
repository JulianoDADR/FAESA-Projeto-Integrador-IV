# Atualizações do relatório para o C3 (textos prontos para colar)

O relatório (`docs/Relatorio_AgroAnalise_Projeto_Integrador_IV.docx`) **não foi editado**. Abaixo estão textos no
estilo do relatório, organizados pela seção onde entrariam. Todos os números vêm dos arquivos indicados e foram
gerados por execução real em 15/11/2026; se o grupo rodar de novo, confira se mudaram. Trechos entre colchetes
dependem de ações do grupo (deploy, testes com pessoas).

---

## Seção 6.3 (Limites do MVP): acrescentar ao final

> Durante o desenvolvimento do MVP foi incluído um módulo demonstrativo de mapa de riscos da região (alagamento,
> chuvas intensas, incêndio, deslizamento de terra e pragas), com áreas de risco simuladas e orientações gerais de
> prevenção que indicam a entidade oficial a consultar. O módulo não altera o escopo do classificador, que continua
> utilizando apenas as três variáveis monitoradas, não emite recomendação agronômica e não utiliza o modelo de
> linguagem para gerar orientações. A localização do usuário, quando autorizada, é processada apenas no navegador.
> A justificativa e os limites dessa ampliação estão registrados em `docs/AMPLIACAO_DE_ESCOPO.md`.

## Seção 7.2 (Levantamento e curadoria dos dados): acrescentar

> Como o circuito com Arduino não estava montado até o MVP, todos os dados utilizados foram simulados e identificados
> como tais na interface, no banco de dados e nos arquivos. O conjunto de treino contém 3.000 amostras geradas com
> semente fixa, rotuladas por regras documentadas a partir de faixas provisórias de demonstração, com ruído de
> medição na rotulagem para evitar um problema trivial. As faixas não constituem parâmetros agronômicos validados e
> dependem da validação prevista na seção 8.3.

## Seção 7.4 (Treinamento e avaliação do modelo): acrescentar

> Foi utilizada uma árvore de decisão (scikit-learn 1.9.1, profundidade máxima 8, mínimo de 5 amostras por folha),
> escolhida pela interpretabilidade. A divisão foi de 80% para treino e 20% para teste, estratificada. Para atender
> à meta de revocação da classe Vermelho, foram comparados um peso maior para a classe crítica e um limiar
> conservador de decisão; a configuração foi escolhida por validação cruzada estratificada com cinco partições
> apenas no conjunto de treino (peso 3 para a classe Vermelho, sem limiar adicional), e o conjunto de teste foi
> utilizado uma única vez. No teste, a revocação da classe Vermelho foi de 0,922 (intervalo de confiança de 95%,
> método de Wilson: 0,883 a 0,949), com precisão de 0,817, acurácia de 0,760 e F1 macro de 0,732; sem o ajuste, a
> revocação era de 0,809. A linha de base (classe majoritária) obteve acurácia de 0,428 e F1 macro de 0,200. Como
> referência de teto, a própria regra de rotulagem aplicada às leituras sem ruído obteve acurácia de 0,818. Uma busca
> mais ampla de hiperparâmetros (240 combinações) indicou outra configuração, que atingiu a meta na validação cruzada
> por margem pequena e obteve revocação de 0,887 no teste; o modelo em produção não foi substituído, para não
> selecionar o modelo com base no conjunto de teste. Como os rótulos derivam de regras sobre as mesmas variáveis de
> entrada, esses resultados validam o pipeline de classificação, e não a eficácia agronômica em campo.
> (Fontes: `docs/avaliacao/classificador.md`, `prototipo/ml/saida/metricas.json`.)

## Seção 6.4 (Componente de IA, avaliação da camada de explicação): acrescentar

> A camada de explicação foi avaliada em 30 cenários (24 válidos, cobrindo as três classes e as duas espécies, e 6
> casos de borda: dado ausente, valor fora de faixa e três tentativas de injeção de instrução). Os seis casos de
> borda foram recusados pela validação de entrada e nenhum chegou ao modelo de linguagem. Para medir o filtro de
> saída de forma reprodutível, utilizou-se um conjunto de respostas escritas e rotuladas manualmente, incluindo
> respostas inadequadas (incoerentes com a classe, com dose ou produto, longas ou em outro idioma): o filtro bloqueou
> 14 de 15 respostas inadequadas e aceitou 7 de 9 adequadas; a resposta inadequada que passou era um falso alarme
> sutil na classe Verde, limitação inerente a um filtro baseado em palavras. A avaliação revelou três falhas no
> filtro, corrigidas e registradas (ordens de manejo sem números, detecção de idioma que recusava frases curtas em
> português e mensagens da classe Vermelho sem pedido de verificação da área). Falhas da API (tempo esgotado, limite
> do plano, erro do servidor e resposta inesperada) resultaram sempre na mensagem-padrão.
> [Acrescentar o resultado do modo ao vivo com o GroqCloud, com data, modelo, tokens e revisão humana, após rodar
> `python ml/avaliar_llm.py --ao-vivo`.] (Fonte: `docs/avaliacao/llm.md`.)

## Seção 7.6 (Testes de software): acrescentar

> O MVP conta com 215 testes automatizados (pytest), todos aprovados na última execução, executados também no
> GitHub Actions a cada envio ao repositório, sem segredos e com o modelo de linguagem sempre simulado. Os testes
> cobrem validação de leituras, protocolo serial e calibração, regra de decisão da classe Vermelho, integração entre
> API, banco, classificador e camada de explicação, chamadas HTTP ao provedor do LLM (limite do plano, tempo esgotado,
> resposta malformada), ingestão autenticada e idempotente, configuração do Turso/libSQL e fail-soft do banco na
> demonstração, teste de ponta a ponta com Arduino simulado em porta virtual (gateway, API, classificação e painel),
> e situações de falha: sensor desconectado, mensagem serial incompleta, valor fora do intervalo, ausência de dados
> recentes, queda de rede do gateway, indisponibilidade do LLM e banco fora do ar. A tabela de cenários, resultado
> esperado, obtido e situação está em `docs/testes.md`.

## Seção 8.4 (Arquitetura de implantação): acrescentar

> A aplicação será publicada como função Python na Vercel, com as páginas servidas pela própria API e persistência
> opcional no Turso/libSQL; o modelo `modelo.pkl` versionado foi regenerado com Python 3.13 e a mesma versão do
> scikit-learn usada na execução. O serviço ficará em [URL pública], com verificação de saúde em `/saude` (incluindo
> `banco_disponivel`, sem expor credenciais). Para que a demonstração não fique sem dados quando nenhum gateway
> estiver enviando, a fonte simulada é o padrão; com `FONTE_LEITURAS=banco`, uma carga inicial de 72 horas simuladas
> pode ser gerada por `app/semear.py`. Falhas de banco não derrubam as páginas, `/status`, `/classificar` ou
> `/metricas` quando a fonte é simulada; as rotas de banco respondem 503. Foram adotados limite de requisições por
> endereço, tamanho máximo de requisição, cabeçalhos de segurança, teto de chamadas ao LLM e recursos de demonstração
> controlados por variável de ambiente. O teste de fumaça contra a URL pública obteve [resultado].
> (Fontes: `docs/DEPLOY.md`, `docs/ARQUITETURA.md`.)

## Seção 9.2 (Indicadores de impacto): acrescentar após o Quadro 5

> Os indicadores foram calculados por script a partir da planilha de coleta e da API em operação. Na etapa de MVP:
> adoção autônoma de [X%] e clareza percebida de [Y%], com [N] participantes [produtores / testes de protótipo];
> disponibilidade de leituras válidas de [Z%] em 72 horas [com leituras do alimentador de demonstração, o que mede a
> operação do sistema e não sensores reais]; revocação da classe Vermelho de 0,922 no conjunto de teste, com a
> limitação de que o rótulo é derivado de regras. Os indicadores de água e de perdas permanecem como plano de
> mensuração e indicador de longo prazo, sem resultado numérico no semestre.
> (Fontes: `docs/usabilidade/indicadores.md`, `docs/usabilidade/analise_de_impacto.md`.)

## Seção 10.1 (Privacidade): acrescentar

> No mapa de riscos, a localização do usuário só é solicitada mediante ação explícita e texto de consentimento, é
> processada exclusivamente no navegador e não é enviada ao servidor, ao modelo de linguagem nem a registros; a API
> recebe apenas o identificador da região. As imagens de mapa são obtidas diretamente do OpenStreetMap pelo
> navegador, o que expõe ao provedor o endereço IP e a área visualizada, fato informado ao usuário.

## Seção 11 (Plano de trabalho): atualizar a linha do C3

> MVP com aplicação web, simulador ao vivo, visão do agricultor com leitura em voz alta, persistência, ingestão
> autenticada, gateway com modo simulado, avaliação do classificador e da camada de explicação, 215 testes
> automatizados com integração contínua, deploy com URL pública [URL] e análise de impacto.
