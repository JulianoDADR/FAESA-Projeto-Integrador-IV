# Projeto Integrador IV
Feito por: Cauan Henrique Damacena, Eduardo Rangel Malaquias Rodrigues, Guilherme de Souza Paiva, Juliano De Andrade Dantas Rodrigues, Rubiale Filho de Melo


## 🚜 AgroAnálise
O AgroAnálise é o Produto Mínimo Viável (MVP) de um sistema IoT com Inteligência Artificial que funciona como um "companheiro virtual" para agricultores familiares com baixo letramento digital.

## 🎯 Objetivo
Cruzar dados climáticos do solo e do ar para prever riscos à colheita (com foco inicial na cultura do Café) e devolver a informação no formato de um semáforo simples (Verde, Amarelo, Vermelho), eliminando a necessidade de o agricultor ler gráficos complexos.

## 🛠️ Stack Tecnológico e Arquitetura
A arquitetura do projeto é dividida nas seguintes tecnologias:
* **Hardware (Coleta):** Arduino equipado com sensor de umidade do solo (higrômetro) e sensor DHT11 para medir temperatura e umidade do ar.
* **Comunicação:** Biblioteca `PySerial` para recepção dos dados do Arduino direto para o computador/servidor local via USB.
* **Processamento e Banco de Dados:** `Pandas` e `NumPy` para limpeza e tratamento dos dados, armazenados em tabelas nativas do `SQLite3`.
* **Inteligência Artificial:** Modelo preditivo treinado com `Scikit-Learn` (Regressão) para calcular os riscos com base no histórico climático e agronômico.

## ⚙️ Estrutura do Sistema
1. **Coleta:** O código C++ (`.ino`) lê os sensores e imprime os dados na porta Serial.
2. **Integração:** O script Python roda em loop capturando os dados e tratando possíveis erros de conexão com o Pandas.
3. **Previsão:** Os valores limpos são passados para o modelo de Machine Learning (`.pkl`), que avalia as regras ideais da planta e devolve o status.
4. **Interface:** Retorno visual simples baseado em cores: Verde (Tudo certo), Amarelo (Atenção) ou Vermelho (Ação imediata).