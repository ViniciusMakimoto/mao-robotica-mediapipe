#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pwm = Adafruit_PWMServoDriver();

// Mínimo e máximo de pulso em "ticks" para o PCA9685
const int servoMin = 150;  // fechado
const int servoMax = 600;  // aberto

// Canais atribuídos aos dedos (0–4)
const int canalPolegar = 0;
const int canalIndicador = 1;
const int canalMedio     = 2;
const int canalAnelar    = 3;
const int canalMinimo    = 4;

String inputString = "";
bool stringCompleta = false;

void setup() {
  Serial.begin(9600);
  pwm.begin();
  pwm.setPWMFreq(50);  // Frequência de 50 Hz para servos

  inputString.reserve(50);
}

void moverDedo(int canal, int estado) {
  int valor = estado == 1 ? servoMax : servoMin;
  pwm.setPWM(canal, 0, valor);
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

  if (stringCompleta) {
    int estados[5];
    int index = 0;

    char *ptr = strtok((char*)inputString.c_str(), ",");
    while (ptr != NULL && index < 5) {
      estados[index++] = atoi(ptr);
      ptr = strtok(NULL, ",");
    }

    // Mapeia os estados para os canais do PCA9685
    moverDedo(canalPolegar,  estados[0]);
    moverDedo(canalIndicador, estados[1]);
    moverDedo(canalMedio,     estados[2]);
    moverDedo(canalAnelar,    estados[3]);
    moverDedo(canalMinimo,    estados[4]);

    inputString = "";
    stringCompleta = false;
  }
}
