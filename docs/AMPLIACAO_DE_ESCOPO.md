# Ampliação de escopo: mapa de riscos da região

**Situação:** implementado no protótipo como **módulo demonstrativo**. O grupo decide se o relatório (C1) é
atualizado para incluí-lo (sugestão de texto em `docs/ATUALIZACOES_RELATORIO_C3.md`, Etapa 9).

## O que foi acrescentado

Uma página `mapa.html` com áreas de risco **simuladas** na região do usuário (alagamento, chuvas intensas, incêndio,
deslizamento de terra e pragas), orientações **gerais** de prevenção e a fonte oficial a consultar em cada caso.
Os talhões aparecem no mapa com o semáforo, para cruzar a lavoura com os riscos da região.

## Por que é uma ampliação

O relatório (seções 6.2 e 6.3) delimita o MVP ao monitoramento de três variáveis (umidade do solo, temperatura e
umidade do ar) e à classificação em três estados. O mapa traz informação de contexto que não vem dos sensores.

## Limites mantidos (não mudam com o mapa)

- **O classificador continua só com as 3 variáveis.** Os riscos do mapa não entram no cálculo do semáforo.
- **Nada de recomendação agronômica:** as orientações são gerais e fixas (`prototipo/app/riscos/orientacoes.json`),
  sem produto, dose, volume, calendário de manejo nem diagnóstico de praga ou doença. **O LLM não gera esses textos.**
- **Dados simulados**, determinísticos por região e por dia, sempre marcados como simulados. Aviso visível em todo o
  módulo: “Dados simulados. Não use para decisões de segurança. Em emergência, ligue para a Defesa Civil (199) ou
  para o Corpo de Bombeiros (193).”
- **Privacidade (LGPD):** a localização só é pedida com um toque no botão e com texto de consentimento; fica no
  navegador (centraliza o mapa e escolhe a região mais próxima); a API recebe apenas o identificador da região
  (`GET /riscos/{regiao_id}`). Comprovado com captura de rede no Chrome: nenhum pedido ao servidor contém a
  coordenada. As imagens do mapa vêm do OpenStreetMap, que vê o IP e a área vista (declarado em “Sobre e limites”).

## Pendências para o grupo antes do C3

1. **Revisão humana das orientações** (`revisado_por_humano` está `false`), de preferência com alguém da Defesa
   Civil, do Corpo de Bombeiros ou do Incaper.
2. **Números de emergência (199 e 193) confirmados em fonte oficial em 15/11/2026** (CBMES, 21/01/2026; MCom,
   11/09/2026). Falta apenas a revisão humana dos textos das orientações.
3. Decidir se o relatório incorpora o módulo ou se ele fica só como demonstração.
4. Se houver dados reais no futuro, implementar `ProvedorReal` a partir de `docs/riscos_fontes_reais.md`.
