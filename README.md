# 🌱 AgroAnálise: Inclusão Digital no Campo com IoT e Machine Learning

O **AgroAnálise** é o Produto Mínimo Viável (MVP) de um sistema integrado de Inteligência Artificial e Internet das Coisas (IoT). Ele atua como um "companheiro virtual" para agricultores familiares com baixo letramento digital, transformando dados complexos de solo e clima em alertas visuais simples.

---

## 🎯 1. Escopo e Regras de Negócio
* **Público-alvo:** Agricultores familiares que possuem letramento digital baixo ou nulo.
* **Cultura Inicial:** Plantações de Café (Arábica/Conilon), devido à sua alta sensibilidade a variações de temperatura e umidade.
* **Variáveis Medidas e Processadas:** Umidade do solo, temperatura do ambiente e umidade relativa do ar.
* **Entrega de Valor (Interface):** Um sistema visual simplificado no formato de semáforo (🟢 Verde = Ideal, 🟡 Amarelo = Atenção, 🔴 Vermelho = Ação Crítica), eliminando a necessidade de leitura de gráficos complexos por parte do produtor.

## 🌍 2. Justificativa e Indicadores de Impacto na Comunidade
O projeto justifica-se pela promoção da inclusão digital no campo, trabalhando dados complexos no *backend* para entregar uma interface intuitiva no *frontend*. 
Para mensurar o sucesso e a adoção da solução pela comunidade agrícola local, serão monitorados os seguintes **Indicadores de Impacto**:
* **Impacto Tecnológico/Social:** Taxa de adoção autônoma (número de propriedades de agricultura familiar que conseguem operar o sistema sem necessidade de suporte técnico contínuo).
* **Impacto Econômico e Ambiental:** Estimativa percentual de redução no desperdício de água de irrigação (eficiência hídrica) guiada pelos alertas preventivos.
* **Impacto Produtivo:** Redução da taxa de perda de safras por estresse hídrico ou térmico tardiamente identificado.

<<<<<<< HEAD
## 📚 3. Fontes de Dados e Referências Agronômicas
* **EcoCrop (FAO) e Kaggle:** Bases de dados contendo limites mínimos, máximos e ideais de temperatura, necessidade hídrica e características do solo.
* **INMET e Embrapa (ZARC):** Utilização de dados meteorológicos e parâmetros oficiais do Zoneamento Agrícola de Risco Climático para o cultivo do café.

## ⚙️ 4. Metodologia Aprofundada e Avaliação (Eval) do Componente de IA
O desenvolvimento do sistema seguirá uma arquitetura integrada dividida em três camadas principais:
* **Camada de Hardware (Coleta):** Utilização de microcontrolador (plataforma Arduino) equipado com sensor de umidade do solo (higrômetro) e sensor DHT11 para temperatura/umidade do ar.
* **Camada de Processamento (Backend):** Um script em linguagem Python receberá as leituras via comunicação `PySerial`. As bibliotecas `Pandas` e `NumPy` farão o tratamento de ruídos para o armazenamento em banco de dados relacional (SQLite3).
* **Inteligência Artificial e Avaliação (Eval):** O motor preditivo será desenvolvido com `Scikit-Learn` (modelo classificador para prever o risco da lavoura nos três estados do semáforo).
    * **Metodologia de Avaliação (Eval):** Para atestar a viabilidade e a confiabilidade da IA, o conjunto de dados (dataset simulado/histórico) será dividido na proporção clássica de 80% para treinamento e 20% para teste (`train_test_split`). 
    * O modelo será rigorosamente validado utilizando **Métricas de Classificação**:
        * **Matriz de Confusão:** Para mapear onde a IA comete erros específicos (ex: classificar o solo como "Atenção" quando deveria ser "Ação Crítica").
        * **Precision e Recall:** Métricas vitais para evitar **Falsos Positivos** (alertar o produtor para irrigar quando a terra já está úmida, desperdiçando água) e **Falsos Negativos** (não alertar o produtor quando a planta está morrendo de sede).
        * **F1-Score e Accuracy:** Para garantir o balanceamento global na previsão correta do risco.

## 📅 5. Plano de Trabalho (Organizado por Checkpoints do PI-IV)
O cronograma de desenvolvimento foi estruturado com base nas entregas exigidas pela disciplina:

* **Checkpoint 1 (C1) – Escopo, Repositório e Levantamento:**
    * Criação e atualização do repositório no GitHub.
    * Definição clara das regras de negócio, arquitetura de hardware/software e os indicadores de impacto na comunidade.
    * Levantamento bibliográfico e determinação dos parâmetros climáticos ideais para a cultura do café (Referências da Embrapa/EcoCrop).

* **Checkpoint 2 (C2) – Implementação IoT, Integração e Avaliação da IA (Eval):**
    * Montagem física dos sensores no Arduino e estabelecimento da comunicação com o Python via PySerial.
    * Estruturação do banco de dados SQLite e geração/limpeza do dataset com Pandas.
    * **Foco central de IA (Eval):** Treinamento do modelo de classificação no Scikit-Learn e aplicação das métricas de avaliação detalhadas na metodologia (Matriz de Confusão, Precision e Recall) para comprovar a eficácia analítica do sistema.

* **Checkpoint 3 (C3) – Interface, Testes Finais e Documentação:**
    * Desenvolvimento do *frontend* simplificado (A lógica visual do "Semáforo Virtual").
    * Testes de integração fim-a-fim (Hardware captando dado ➡️ Python processando ➡️ IA avaliando ➡️ Interface mudando a cor).
    * Formatação da documentação final e preparação da apresentação para a banca avaliadora.
=======
## ⚙️ Estrutura do Sistema
1. **Coleta:** O código C++ (`.ino`) lê os sensores e imprime os dados na porta Serial.
2. **Integração:** O script Python roda em loop capturando os dados e tratando possíveis erros de conexão com o Pandas.
3. **Previsão:** Os valores limpos são passados para o modelo de Machine Learning (`.pkl`), que avalia as regras ideais da planta e devolve o status.
4. **Interface:** Retorno visual simples baseado em cores: Verde (Tudo certo), Amarelo (Atenção) ou Vermelho (Ação imediata).
>>>>>>> 5cbead0e4949ac136b2f8a0b656f72b118a08fe8
