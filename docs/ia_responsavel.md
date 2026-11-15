# IA responsável no AgroAnálise

Resumo do que o sistema faz para usar IA com responsabilidade (relatório, seção 10), com o arquivo ou teste que
comprova cada ponto.

## 1. Papel de cada IA

| Componente | Decide a cor? | O que faz | Comprovação |
|---|---|---|---|
| Classificador (árvore de decisão, Scikit-Learn) | **Sim** | Classifica solo, temperatura e ar em Ideal, Atenção ou Ação crítica | `docs/avaliacao/classificador.md` |
| LLM (Groq, `llama-3.1-8b-instant`) | **Não** | Reescreve a classe já decidida em até 2 frases simples | `docs/avaliacao/llm.md`; `app/explicacao.py` |

Sem o LLM (sem chave, falha, cota estourada ou saída rejeitada), o semáforo funciona com mensagens-padrão.

## 2. Privacidade (LGPD)

- A operação básica não coleta dados pessoais: só leituras ambientais e o identificador do ponto.
- O LLM recebe apenas a classe, a espécie e três números (nenhum dado do usuário).
- **Localização no mapa de riscos:** só com um toque no botão e texto de consentimento; fica no navegador; a API
  recebe só o nome da região. Comprovado com captura de rede no Chrome (nenhum pedido ao servidor com a coordenada)
  e por teste (`testes/test_riscos.py`). As imagens do OpenStreetMap expõem o IP e a área vista (declarado na página “Sobre”).
- Visão e talhão escolhidos ficam na URL; nada é guardado no aparelho (`testes/test_interface.py`).
- Testes de usabilidade sem nome nem gravação: participante vira código (`docs/usabilidade/roteiro_teste.md`).

## 3. Segurança e prompt injection

- Entrada do LLM só estruturada e validada; campos extras e texto livre são recusados com 422 antes de chegar ao
  modelo. Na avaliação, os 6 casos de borda (incluindo 3 tentativas de injeção) foram recusados e **nenhum chegou
  ao LLM**.
- Instruções do sistema fixas no servidor; saída limitada a 120 tokens e filtrada.
- Ingestão de leituras só com token de dispositivo; limite de pedidos, corpo máximo e cabeçalhos de segurança.
- Segredos só em variáveis de ambiente; a chave nunca aparece em log (`testes/test_llm_http.py`).

## 4. Transparência e limites

- Faixa “DADOS SIMULADOS · MODO DEMONSTRAÇÃO” em todas as páginas; cada leitura traz a origem.
- As “proporções” mostradas não são confiança: são a fração de amostras de treino parecidas (ponderada).
- Selo dizendo se a mensagem veio do LLM ou é a mensagem-padrão.
- O sistema avisa quando a entrada sai do intervalo visto no treino.
- **O que o sistema não faz:** não aciona irrigação, não diagnostica doenças nem pragas, não estima produtividade,
  não dá recomendação agronômica individualizada (produto, dose, volume) e não substitui a assistência técnica.
  A decisão de manejo é sempre do produtor.

## 5. Limites conhecidos e vieses

- **Rótulos por regra sobre as mesmas variáveis:** as métricas validam o pipeline, não a eficácia em campo.
- **Faixas provisórias** escolhidas para demonstração, não validadas com ZARC, Embrapa ou orientação agronômica.
- **Filtro do LLM por palavras:** não entende o sentido. Na avaliação mock, deixou passar 1 de 15 respostas ruins
  (um falso alarme sutil no Verde) e bloqueou 2 de 9 boas (com negação). A qualidade do Groq real ainda não foi
  medida (`python ml/avaliar_llm.py --ao-vivo`).
- **Regra conservadora:** reduz Vermelhos perdidos, mas aumenta falsos alarmes (precisão do Vermelho 0,817).
- **Variáveis ausentes:** precipitação local, radiação solar, estágio fenológico, textura do solo, profundidade das raízes.
- **Português do Brasil e duas espécies de café:** outras culturas e regiões exigiriam novo levantamento.

## 6. Custo e sustentabilidade

- Plano gratuito do Groq: cache por faixa de valores, respostas curtas, teto por minuto e por dia; uso do dia
  (chamadas e tokens) em `GET /saude`.
- Servidor gratuito: sem custo fixo, com limitações declaradas (sono, disco efêmero).
- Custos do hardware: **[a registrar pelo grupo quando o circuito for montado]** (relatório, seção 10.4).
