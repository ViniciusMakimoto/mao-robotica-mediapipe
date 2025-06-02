#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Canais atribuídos aos dedos (0–4)
const int canalPolegar = 4;
const int canalIndicador = 3;
const int canalMedio     = 2;
const int canalAnelar    = 1;
const int canalMinimo    = 0;

// Mínimo e máximo de pulso em "ticks" para o PCA9685
struct DedoConfig {
  int canal;
  int servoMin;
  int servoMax;
};

// Configuração individual para cada dedo
DedoConfig dedos[] = { 
  {canalMinimo, 100, 500},  // Mínimo
  {canalAnelar, 500, 100}, // Anelar
  {canalMedio, 100, 500}, // Médio
  {canalIndicador, 150, 450}, // Indicador
  {canalPolegar, 100, 500} // Polegar
};

String inputString = "";
bool stringCompleta = false;

bool modoAnalogico = false;
float estados[5];    // agora float, sem contar o modo no índice 0

void moverDedo(int dedoIndex, float estado) {
  if (dedoIndex < 0 || dedoIndex >= 5) return;

  DedoConfig& d = dedos[dedoIndex];
  int valorPWM;

  if (modoAnalogico) {
    // estado ∈ [0.0, 1.0], mapeia para [servoMin, servoMax]
    valorPWM = d.servoMin + estado * (d.servoMax - d.servoMin);
  } else {
    // modo binário: tudo aberto (0→min) ou tudo fechado (1→max)
    valorPWM = (estado < 0.5f) ? d.servoMin : d.servoMax;
  }

  pwm.setPWM(d.canal, 0, valorPWM);
}

void setup() {
  Serial.begin(9600);
  pwm.begin();
  pwm.setPWMFreq(50);  // Frequência de 50 Hz para servos

  inputString.reserve(50);
}

void loop() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    if (inChar == '\n') {
      stringCompleta = true;
      break;
    } else {
      inputString += inChar;
    }
  }

  // ... seu código de leitura da string permanece igual ...
if (stringCompleta) {
  // quebra a string em tokens
  char* input = (char*)inputString.c_str();
  char* ptr = strtok(input, ",");

  // extrai o modo
  char modo = ptr[0];
  modoAnalogico = (modo == 'A');
  ptr = strtok(NULL, ",");

  // preenche os estados dos 5 dedos como float
  int idx = 0;
  while (ptr != NULL && idx < 5) {
    estados[idx++] = atof(ptr);    // agora atof, para capturar decimais em analógico
    ptr = strtok(NULL, ",");
  }

  // chama moverDedo para cada dedo
  for (int i = 0; i < 5; i++) {
    moverDedo(i, estados[4 - i]);
  }

  // limpa
  inputString = "";
  stringCompleta = false;
  }
}
