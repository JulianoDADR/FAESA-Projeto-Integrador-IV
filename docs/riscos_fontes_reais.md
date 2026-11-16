# Fontes reais candidatas para o mapa de riscos (a verificar)

O `ProvedorReal` (`prototipo/app/riscos/provedores.py`) **não está implementado**. Esta lista só aponta onde
procurar. **Nenhum endereço de API foi conferido**: onde está escrito “verificar”, alguém do grupo precisa abrir o
site oficial, confirmar se há dados abertos, o formato, a licença, a frequência de atualização e as regras de uso,
e registrar tudo em `docs/fontes.md` com a data de acesso.

| Risco | Entidade candidata | O que pode oferecer (a confirmar) | Situação |
|---|---|---|---|
| Chuvas intensas | INMET (Instituto Nacional de Meteorologia) | Avisos meteorológicos por área | verificar formato, licença e endereço de dados |
| Alagamento e deslizamento | CEMADEN (Centro Nacional de Monitoramento e Alertas de Desastres Naturais) | Alertas de risco geo-hidrológico por município | verificar |
| Incêndio | INPE, Programa Queimadas | Focos de calor detectados por satélite | verificar |
| Alagamento, deslizamento, chuvas | Defesa Civil do Espírito Santo (inclui o sistema de alerta estadual, citado no site como ALERTA!ES) | Alertas e boletins estaduais | verificar se há dados abertos ou só avisos em página |
| Pragas | Incaper | Boletins e orientações técnicas por região | verificar; não usar para diagnóstico automático |

## Regras para quando for implementar

- Buscar as camadas **no servidor, por região** (nunca com a coordenada do usuário).
- Mostrar a fonte e a data de cada camada; se a fonte falhar, mostrar “dados indisponíveis”, **nunca** trocar
  silenciosamente para dados simulados.
- Manter as orientações gerais e revisadas por humanos; nada de recomendação agronômica específica.
- Respeitar limites de uso e citar a fonte conforme a licença de cada serviço.
