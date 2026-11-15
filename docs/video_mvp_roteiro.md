# Roteiro do vídeo do MVP (C3)

Duração alvo: **6 minutos** (máximo 7). Narração curta, em frases simples. Cada cena indica o critério da rubrica
do C3 que ela atende. Responsável sugerido: Guilherme (Quadro 7). Tudo o que aparece é **simulado**: diga isso.

| Critério da rubrica | Peso | Cenas |
|---|---|---|
| Funcionalidade, usabilidade e inovação | 35% | 3, 4, 5, 6, 7 |
| Qualidade da IA e sua avaliação | 25% | 8, 9 |
| Testes automatizados | 15% | 10 |
| Deploy (URL pública) + documentação/código | 15% | 2, 11 |
| Impacto e IA responsável | 10% | 1, 12 |

## Cenas

| # | Tempo | Tela | Narração (sugestão) |
|---|---|---|---|
| 1 | 0:00–0:30 | Slide ou `index.html` | “No Espírito Santo, três em cada quatro estabelecimentos rurais são de agricultura familiar, e quase oito em cada dez deles não recebem orientação técnica (IBGE, Censo 2017). O AgroAnálise mostra a situação do cafezal num semáforo simples.” |
| 2 | 0:30–0:55 | URL pública no navegador e `docs/ARQUITETURA.md` | “Este é o MVP publicado na internet. São quatro camadas: sensores, gateway no computador do produtor, a API na nuvem com a IA, e o semáforo no celular.” |
| 3 | 0:55–1:50 | `index.html` → **Iniciar demonstração** (avance com →) | “O modo apresentação mostra os estados. Ideal é círculo verde; Atenção, triângulo amarelo; Ação crítica, octógono vermelho. Cor, palavra, ícone e forma dizem a mesma coisa. Sem leitura recente, fica cinza: nunca presume que está tudo bem.” |
| 4 | 1:50–2:25 | `agricultor.html` no celular, tocar **Ouvir** | “Para o produtor, uma tela só: semáforo grande, uma frase e o botão Ouvir, que lê a mensagem em voz alta.” |
| 5 | 2:25–2:55 | `talhoes.html` (mostrar filtro e 2×) | “Oito pontos da propriedade ao vivo, os que pedem mais cuidado primeiro.” |
| 6 | 2:55–3:30 | Terminal: gateway `--simulado` + painel; depois parar o gateway | “O caminho real já funciona com um Arduino simulado: o gateway valida as linhas, descarta as defeituosas, guarda e envia com token. Quando o gateway para, o painel fica cinza.” (use `MINUTOS_DESATUALIZADO=1` numa gravação local) |
| 7 | 3:30–4:00 | `mapa.html` (camadas, toque numa área) | “Um módulo demonstrativo mostra riscos simulados da região com orientações gerais e a fonte oficial. A localização fica só no aparelho.” |
| 8 | 4:00–4:40 | `ia.html`: classificar, mostrar proporções e selo; **Simular falha do LLM** | “Quem decide a cor é o classificador. O LLM só explica. Se o LLM cair, a mensagem-padrão entra e o semáforo continua.” |
| 9 | 4:40–5:15 | `avaliacao.html` e `docs/avaliacao/llm.md` | “Com o ajuste para a classe crítica, a revocação do Vermelho foi de 0,81 para 0,92, com mais falsos alarmes. Os dados são simulados: isto valida o pipeline, não a lavoura. Na avaliação do LLM, nenhuma tentativa de injeção chegou ao modelo, e o filtro bloqueou 14 de 15 respostas ruins.” |
| 10 | 5:15–5:35 | Terminal `pytest -q` e a aba Actions do GitHub | “São [205] testes automatizados, rodando a cada envio ao GitHub.” |
| 11 | 5:35–5:50 | Terminal `scripts/teste_fumaca.py --url <url>` | “O teste de fumaça confere a URL pública: [23 de 23] verificações.” |
| 12 | 5:50–6:20 | `sobre.html` e `docs/usabilidade/indicadores.md` | “O sistema não aciona irrigação nem recomenda produto ou dose; a decisão é do produtor. [Resultado do teste com pessoas.] Próximos passos: montar e calibrar o sensor e validar as faixas com orientação técnica.” |

Os números entre colchetes devem ser conferidos na hora da gravação.

## Checklist de gravação

- [ ] Tela em 1920×1080 (1080p); zoom do navegador em 125% para o texto ficar legível; celular espelhado ou emulação
      de celular (DevTools) para as cenas 4 e 5.
- [ ] **Nunca mostrar** o arquivo `.env`, variáveis com chave ou token, o painel de variáveis do Render nem o
      console do Groq. Feche abas e notificações.
- [ ] Abrir antes a URL pública (o servidor gratuito pode demorar a acordar) e deixar as abas na ordem das cenas.
- [ ] Rodar `pytest -q` e o teste de fumaça antes e conferir os números da narração.
- [ ] Para a cena 6, gravar localmente com `FONTE_LEITURAS=banco` e `MINUTOS_DESATUALIZADO=1`.
- [ ] Falar “dados simulados” pelo menos nas cenas 3, 6, 7 e 9.
- [ ] Não afirmar economia de água, ganho de produtividade nem eficácia em campo.
- [ ] Publicar no YouTube (público ou não listado, conforme o edital) e colocar o link no README e no AVA.
