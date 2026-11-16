/*
  AgroAnálise - leitura de solo e clima para o gateway (Projeto Integrador IV, FAESA)

  *** NÃO TESTADO EM HARDWARE ***
  Este sketch foi escrito antes da montagem do circuito. Compila na teoria, mas ninguém do grupo o carregou
  num Arduino ainda. Quem montar o circuito deve testar, corrigir o que for preciso e registrar o resultado.

  Saída serial (9600 baud), uma linha por leitura, no protocolo do gateway (prototipo/gateway/protocolo.py):
      P:A;N:128;S:432;T:27.5;U:61.0
    P = ponto de monitoramento (talhão), N = número de sequência (0..65535),
    S = leitura BRUTA do sensor de umidade do solo (ADC 0..1023, média de 5 amostras),
    T = temperatura do ar (°C, DHT11), U = umidade relativa do ar (%, DHT11). "nan" quando o DHT11 falha.

  Esquema de ligação (texto):
    Sensor de umidade do solo (módulo analógico, 3 pinos):
      VCC -> 5V do Arduino    (ou pino digital D7 para ligar só na hora de medir e reduzir a corrosão)
      GND -> GND
      AO  -> A0
    DHT11 (módulo de 3 pinos):
      VCC  -> 5V
      GND  -> GND
      DATA -> D2 (o módulo já costuma ter o resistor de pull-up de 10 kΩ; se for o sensor solto, coloque um)
    Arduino -> computador do gateway pelo cabo USB.

  Biblioteca necessária: "DHT sensor library" (Adafruit) e "Adafruit Unified Sensor", pelo Gerenciador de Bibliotecas.

  CALIBRAÇÃO PENDENTE (relatório, seção 7.3: etapa essencial):
    A leitura bruta não é uma % universal de água no solo. Para cada tipo de solo:
      1. anote S com o sensor no solo bem seco (ou no ar)       -> bruto_seco
      2. anote S com o solo encharcado (ou o sensor na água)    -> bruto_molhado
      3. passe os dois valores ao gateway: --bruto-seco e --bruto-molhado
    Até lá o gateway usa valores provisórios (850 e 400), que não representam o solo da lavoura.
*/

#include <DHT.h>

const char PONTO[] = "A";               // talhão deste Arduino (um Arduino por ponto de monitoramento)
const uint8_t PINO_SOLO = A0;
const uint8_t PINO_DHT = 2;
const unsigned long INTERVALO_MS = 600000UL;  // 10 minutos entre leituras (para testar na bancada, use 5000UL)
const uint8_t AMOSTRAS_SOLO = 5;

DHT dht(PINO_DHT, DHT11);
uint16_t sequencia = 0;

int lerSoloBruto() {
  long soma = 0;
  for (uint8_t i = 0; i < AMOSTRAS_SOLO; i++) {
    soma += analogRead(PINO_SOLO);
    delay(50);
  }
  return (int)(soma / AMOSTRAS_SOLO);
}

void setup() {
  Serial.begin(9600);
  dht.begin();
  delay(2000);  // o DHT11 precisa de um tempo depois de ligado
}

void loop() {
  int solo = lerSoloBruto();
  float temperatura = dht.readTemperature();  // NAN se a leitura falhar
  float umidadeAr = dht.readHumidity();       // NAN se a leitura falhar
  sequencia++;

  Serial.print("P:");  Serial.print(PONTO);
  Serial.print(";N:"); Serial.print(sequencia);
  Serial.print(";S:"); Serial.print(solo);
  Serial.print(";T:"); if (isnan(temperatura)) Serial.print("nan"); else Serial.print(temperatura, 1);
  Serial.print(";U:"); if (isnan(umidadeAr)) Serial.print("nan"); else Serial.print(umidadeAr, 1);
  Serial.print("\n");

  delay(INTERVALO_MS);
}
