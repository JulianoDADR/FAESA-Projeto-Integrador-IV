# Indicadores de impacto (calculados)

Gerado por `python ml/calcular_indicadores.py` em 2026-11-15T21:24:44+00:00. Planilha: `planilha_coleta.csv` (0 participantes com consentimento).

| Dimensão | Indicador | Resultado | Meta (relatório, Quadro 5) | Situação |
|---|---|---|---|---|
| Social e usabilidade | Taxa de adoção autônoma | sem dados | ≥ 70% (mínimo de 10 participantes) | — |
| Usabilidade | Clareza percebida (notas 4 ou 5) | sem dados | ≥ 80% | — |
| Operacional | Disponibilidade de leituras válidas (72 h) | sem dados | ≥ 95% | — |
| Confiabilidade da IA | Revocação da classe Vermelho (teste) | 92,2% | ≥ 90% | atingida |
| Econômica e ambiental | Redução do desperdício de água | não medido | sem meta no semestre | plano de mensuração |
| Produtiva | Redução de perdas por identificação tardia | não medido | indicador de longo prazo | futuro |

## Avisos

- Usabilidade: sem participantes ainda.
- Disponibilidade: não medida (rode com --url apontando para a API em operação).
- Revocação do Vermelho: Rótulos gerados por regras sobre as mesmas variáveis de entrada: este resultado valida o pipeline, não a eficácia agronômica em campo.
- Os indicadores de água e de perdas não têm número neste semestre (relatório, seção 9.2). Veja o plano de
  mensuração em `docs/usabilidade/analise_de_impacto.md`.
- Resultados de teste de protótipo, em ambiente controlado; não representam resultados em lavouras.
