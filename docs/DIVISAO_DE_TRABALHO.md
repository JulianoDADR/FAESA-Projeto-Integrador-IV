# Divisão de trabalho para o C3

Proposta baseada no Quadro 7 do relatório (coluna “C3, planejado”). **O grupo pode ajustar.** Cada pessoa commita
com o próprio usuário Git e registra o próprio uso de IA em `docs/uso-de-ia/REGISTRO.md`.

| Integrante | Módulos (pastas) | O que falta fazer no C3 |
|---|---|---|
| **Eduardo** | Backend, banco e testes: `prototipo/app/`, `prototipo/testes/` | Revisar as decisões registradas no REGISTRO; fazer o push da branch `eduardo/c3`; abrir o pull request; acompanhar o CI. |
| **Cauan** | Avaliação do classificador e do LLM: `prototipo/ml/avaliar_*.py`, `docs/avaliacao/` | Revisar os rótulos do banco de respostas do LLM; rodar `python ml/avaliar_llm.py --ao-vivo` com a chave do Groq e fazer a revisão humana; decidir (pela validação cruzada) se o modelo em produção muda. |
| **Guilherme** | Frontend e vídeo: `prototipo/web/`, `docs/video_mvp_roteiro.md` | Revisar textos e telas no celular; gravar e publicar o vídeo do MVP seguindo o roteiro e o checklist. |
| **Juliano** | Gateway, integração e deploy: `prototipo/gateway/`, `prototipo/arduino/`, `docs/DEPLOY.md` | Fazer o deploy na conta do grupo e passar a URL; rodar o teste de fumaça; montar o circuito, carregar o sketch e calibrar o sensor de solo; testar o gateway com o Arduino real. |
| **Rubiale** | Documentação, usabilidade e impacto: `docs/usabilidade/`, `docs/ATUALIZACOES_RELATORIO_C3.md` | Aplicar o teste com pelo menos 10 pessoas; preencher a planilha; rodar `ml/calcular_indicadores.py`; completar a análise de impacto; atualizar o relatório (.docx) com os textos prontos. |

## Pendências que não são de uma pessoa só

- Revisar os textos das orientações do mapa de riscos (`prototipo/app/riscos/orientacoes.json`, campo
  `revisado_por_humano`); os números 199 e 193 já foram confirmados em fonte oficial em 15/11/2026.
- Conferir os limites dos planos gratuitos do Groq, da Vercel e do Turso (`docs/fontes.md`); a política de uso dos
  tiles do OpenStreetMap foi conferida em 15/11/2026 e o uso atual do mapa está compatível.
- Decidir se o mapa de riscos entra no relatório (`docs/AMPLIACAO_DE_ESCOPO.md`).
- Confirmar no AVA a data vigente de entrega do C3 (04/12/2026 pelo edital).
