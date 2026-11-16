# Avaliação do classificador

> **Rótulos gerados por regras sobre as mesmas variáveis de entrada: este resultado valida o pipeline, não a eficácia agronômica em campo.** Todos os dados são **simulados**; as faixas de rotulagem são provisórias.

Gerado por `python ml/avaliar_classificador.py` em 2026-11-15T20:54:51+00:00 (scikit-learn 1.9.1).
Números reais da execução; nada foi ajustado à mão.

## Método

- 3000 amostras simuladas; 80/20 estratificada (random_state=42); validação cruzada estratificada k=5 só no treino.
  Teste: 600 amostras (Verde 147, Amarelo 196, Vermelho 257).
- Busca pequena de hiperparâmetros (240 combinações de profundidade, folha mínima, peso do
  Vermelho e limiar conservador), cada uma avaliada pela média de 5 dobras **só no treino**.
- Critério de escolha: maior F1 macro entre as combinações com revocação média do Vermelho >= 0,90 na validação cruzada.
- O conjunto de teste foi usado **uma vez**, depois da escolha. A revocação do Vermelho tem intervalo de confiança
  de Wilson de 95%.
- Vazamento: Amostras independentes, sem sequência temporal: não há blocos a separar. As leituras do simulador ao vivo não entram no treino.

## Resultado no conjunto de teste

| Modelo | Acurácia | F1 macro | Revocação do Vermelho (IC 95%) | Precisão do Vermelho | Vermelho perdido como Amarelo / Verde |
|---|---|---|---|---|---|
| Modelo escolhido nesta avaliação | 0,777 | 0,759 | 0,887 (0,843 a 0,920) | 0,864 | 26 / 3 |
| Modelo em produção | 0,760 | 0,732 | 0,922 (0,883 a 0,949) | 0,817 | 17 / 3 |
| Regra de referência (teto) | 0,818 | 0,803 | 0,910 (0,869 a 0,940) | 0,893 | 23 / 0 |
| Linha de base (classe majoritária) | 0,428 | 0,200 | 1,000 (0,985 a 1,000) | 0,428 | 0 / 0 |

- **Escolhido nesta avaliação:** profundidade 12, folha mínima
  5, peso do Vermelho 1,
  0,40. Na validação cruzada: F1 macro 0,777 ±
  0,010, revocação do Vermelho 0,902 ±
  0,006.
- **Em produção** (`ml/saida/modelo.pkl`): profundidade 8, folha mínima
  5, peso do Vermelho 3,
  sem limiar. Na validação cruzada: F1 macro 0,761 ±
  0,035, revocação do Vermelho 0,915 ±
  0,017.

Matriz de confusão do modelo escolhido (linhas = real, colunas = previsto; ordem Verde, Amarelo, Vermelho):

| | Verde | Amarelo | Vermelho |
|---|---|---|---|
| **Verde** | 133 | 14 | 0 |
| **Amarelo** | 55 | 105 | 36 |
| **Vermelho** | 3 | 26 | 228 |

## Qual modelo fica em produção

O modelo em produção foi fixado na Etapa 1, **antes** desta avaliação, também por validação cruzada só no treino
(com a profundidade fixa em 8). A busca maior desta avaliação escolheu outra configuração, que atinge a meta na
validação cruzada por margem pequena (revocação do Vermelho 0,902 ±
0,006) e ficou em 0,887 no teste.
Trocar o modelo agora **olhando estes números de teste** seria escolher pelo teste, o que o método proíbe.
Por isso o modelo em produção **não foi trocado automaticamente**. Os dois intervalos de confiança se sobrepõem;
qualquer troca deve ser decidida pelo grupo com base na validação cruzada (por exemplo, preferindo uma margem maior
sobre a meta), e então reavaliada num conjunto de teste novo.

## Efeito do limiar conservador (sem peso extra, no teste; só para leitura, não usado na escolha)

| Limiar do Vermelho | Revocação do Vermelho | Precisão do Vermelho | Acurácia | F1 macro |
|---|---|---|---|---|
| sem limiar | 0,809 | 0,893 | 0,752 | 0,740 |
| 0,50 | 0,821 | 0,894 | 0,757 | 0,744 |
| 0,40 | 0,829 | 0,895 | 0,760 | 0,746 |
| 0,30 | 0,852 | 0,866 | 0,755 | 0,737 |
| 0,20 | 0,903 | 0,808 | 0,747 | 0,717 |
| 0,15 | 0,918 | 0,792 | 0,742 | 0,707 |
| 0,10 | 0,949 | 0,680 | 0,672 | 0,587 |

## As 10 melhores combinações por F1 macro na validação cruzada (média ± desvio das 5 dobras)

| Profundidade | Folha mínima | Peso do Vermelho | Limiar | F1 macro | Revocação do Vermelho | Acurácia |
|---|---|---|---|---|---|---|
| 12 | 10 | 1 | sem limiar | 0,786 ± 0,022 | 0,878 ± 0,010 | 0,799 ± 0,020 |
| 10 | 10 | 1 | sem limiar | 0,782 ± 0,020 | 0,875 ± 0,013 | 0,796 ± 0,018 |
| 12 | 5 | 1 | sem limiar | 0,782 ± 0,014 | 0,876 ± 0,014 | 0,795 ± 0,013 |
| 12 | 10 | 1 | 0,40 | 0,780 ± 0,021 | 0,900 ± 0,019 | 0,796 ± 0,018 |
| 10 | 10 | 1 | 0,40 | 0,778 ± 0,020 | 0,891 ± 0,021 | 0,794 ± 0,018 |
| 10 | 1 | 1 | 0,40 | 0,778 ± 0,015 | 0,861 ± 0,015 | 0,790 ± 0,015 |
| 10 | 1 | 1 | sem limiar | 0,777 ± 0,015 | 0,856 ± 0,013 | 0,790 ± 0,014 |
| 10 | 5 | 1 | sem limiar | 0,777 ± 0,013 | 0,865 ± 0,009 | 0,790 ± 0,012 |
| 10 | 5 | 1 | 0,40 | 0,777 ± 0,010 | 0,887 ± 0,011 | 0,792 ± 0,009 |
| 12 | 5 | 1 | 0,40 | 0,777 ± 0,010 | 0,902 ± 0,006 | 0,793 ± 0,009 |

## Limitações

- **Rótulos por regra:** os rótulos foram gerados por regras sobre as mesmas variáveis de entrada, com ruído de
  medição. A regra de referência (sem ML) é o teto aproximado; o modelo só pode reaprender a regra. **Isto valida o
  pipeline, não a eficácia agronômica em campo.**
- **Dados simulados e faixas provisórias:** não representam lavouras reais nem parâmetros validados (ZARC, Embrapa).
- **Um único sorteio do dataset e uma única divisão de teste:** o desvio na validação cruzada e o intervalo de
  Wilson dão a ordem de grandeza da incerteza, não cobrem dados reais.
- **Variáveis ausentes:** precipitação, radiação, estágio fenológico, textura do solo e profundidade das raízes não
  entram no modelo (relatório, seção 10.3).
