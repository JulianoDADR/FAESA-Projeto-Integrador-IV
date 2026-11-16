# Análise de impacto do AgroAnálise (C3)

> **Modelo.** Só o que já é fato está preenchido (com a fonte). Tudo o que depende dos testes com pessoas ou da
> operação está marcado **[a preencher após os testes]**. Não preencha com estimativas: o edital e o relatório
> pedem resultados reais, mesmo que pequenos. Responsável sugerido: Rubiale (Quadro 7 do relatório).

## 1. Comunidade e problema

**Fato (relatório, seção 9.1; IBGE, Censo Agropecuário 2017, conferido no SIDRA):** o Espírito Santo tinha 108.014
estabelecimentos agropecuários, dos quais 80.775 (74,8%) de agricultura familiar; esses estabelecimentos
concentravam 213.557 das 357.258 pessoas ocupadas na agropecuária do estado (59,8%). Apenas 17.088 estabelecimentos
da agricultura familiar (21,2%) recebiam orientação técnica; 78,8% não recebiam. A agricultura familiar respondeu por
51,0% da produção de Conilon e por 57,6% da produção de Arábica do estado.

**Fato (relatório, seção 9.1; Bliska et al., 2021):** a cafeicultura estava presente em 63.976 dos 108.014
estabelecimentos, e 78,23% das propriedades cafeeiras eram familiares.

**Lacuna declarada no próprio relatório:** esses números não caracterizam o **perfil digital** dos produtores.
Levantamento complementar (acesso à internet, escolaridade, renda, presença do Incaper na região):
**[a preencher após o levantamento documental]**.

## 2. O que o MVP entrega

- Semáforo de três estados (Ideal, Atenção, Ação crítica) com palavra, ícone e forma, e estado “Sem dados
  atualizados” sem cor de avaliação.
- Visão do agricultor com semáforo grande e leitura em voz alta; visão técnica com detalhes.
- Mensagem curta em linguagem simples (LLM só reformula; mensagem-padrão quando ele falha).
- Pipeline previsto no relatório funcionando com o Arduino **simulado** (gateway, banco, ingestão autenticada).
- Mapa de riscos **demonstrativo** (ampliação de escopo, `docs/AMPLIACAO_DE_ESCOPO.md`).

## 3. Indicadores (relatório, Quadro 5)

Números calculados por `prototipo/ml/calcular_indicadores.py` a partir da planilha de coleta e da API. Resultado
atual em `docs/usabilidade/indicadores.md`.

| Indicador | Meta | Resultado | Fonte do resultado |
|---|---|---|---|
| Adoção autônoma (3 tarefas sem ajuda em até 5 min) | ≥ 70% (mín. 10 participantes) | **[a preencher após os testes]** | planilha de coleta |
| Clareza percebida (notas 4 ou 5) | ≥ 80% | **[a preencher após os testes]** | planilha de coleta |
| Disponibilidade de leituras válidas em 72 h | ≥ 95% | **[a preencher após 72 h de operação]** | `GET /disponibilidade` na URL pública |
| Revocação do Vermelho (teste) | ≥ 0,90 | **0,922** (IC 95%: 0,883 a 0,949) | `docs/avaliacao/classificador.md` (dados simulados) |
| Redução do desperdício de água | sem meta no semestre | não medido | plano na seção 5 |
| Redução de perdas por identificação tardia | longo prazo | não medido | indicador futuro |

**Atenção ao interpretar a revocação do Vermelho:** os rótulos foram gerados por regras sobre as mesmas variáveis
de entrada; o número valida o pipeline, não a eficácia agronômica em campo. A disponibilidade, se medida na URL
pública com o alimentador de demonstração ligado, mede a operação do sistema, não sensores reais.

## 4. Resultados dos testes com pessoas

- Participantes (quantidade e perfis, sem dados pessoais): **[a preencher após os testes]**
- Onde as pessoas hesitaram (por tarefa): **[a preencher após os testes]**
- Mudanças feitas na interface por causa do teste: **[a preencher após os testes]**
- Os participantes eram produtores? Se não, declarar que são **testes de protótipo** e não generalizar
  (relatório, seção 9.1): **[a preencher após os testes]**

## 5. Plano de mensuração do desperdício de água (sem número neste semestre)

Do relatório (Quadro 5): comparar o volume de água em períodos ou condições comparáveis, com e sem o apoio do
sistema, registrando método, intervalo e limitações. Proposta para depois do MVP:

1. Escolher uma propriedade parceira e dois talhões parecidos (mesma espécie, idade e tipo de solo).
2. Medir o volume de irrigação (hidrômetro ou tempo × vazão) por várias semanas antes do uso do sistema.
3. Repetir no mesmo período do ano seguinte (ou em paralelo), com o produtor usando o semáforo para decidir
   quando olhar a lavoura; **a decisão de irrigar continua sendo dele**.
4. Registrar chuva, temperatura e manejo para separar o efeito do clima.

Limitação: alertas emitidos não comprovam economia de água (relatório, seção 9.2). Nenhuma economia é afirmada.

## 6. Efeitos não intencionais e riscos

- **Falsa segurança:** um Verde errado pode atrasar uma visita à lavoura. Mitigação: priorizar a revocação do
  Vermelho, mostrar que a decisão é do produtor e estimular a orientação técnica.
- **Excesso de alarmes:** a regra conservadora aumenta os falsos alarmes (precisão do Vermelho 0,817 no teste).
  Isso pode cansar o usuário: **[avaliar nos testes com pessoas]**.
- **Dependência de internet e de servidor gratuito:** o estado “Sem dados atualizados” evita mostrar uma cor velha.
- **Privacidade:** sem dados pessoais na operação básica; localização do mapa só no aparelho.

## 7. ODS relacionados (README)

ODS 9 (indústria, inovação e infraestrutura), ODS 12 (consumo e produção responsáveis) e ODS 8 (trabalho decente e
crescimento econômico). Como o MVP contribui na prática: **[a preencher após os testes, sem exagerar]**.

## 8. Limitações

Dados simulados; faixas provisórias não validadas (ZARC, Embrapa); Arduino não montado e calibração do sensor
pendente; ausência de variáveis como precipitação local, radiação solar, estágio fenológico e textura do solo
(relatório, seção 10.3); testes com poucos participantes e, possivelmente, sem produtores.

## 9. Próximos passos

**[a preencher pelo grupo]** (sugestões: montar e calibrar o sensor; validar as faixas com orientação agronômica;
testar com produtores e técnicos do Incaper; integrar fontes oficiais ao mapa de riscos).
