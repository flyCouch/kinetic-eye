/*
 * PROJECT: Kinetic Eye - Spectralmeter
 * FILE: __FILE__
 * DATE: __DATE__
 * TIME: __TIME__
 */

#include "BluetoothSerial.h"

#define RED_PIN    4
#define GREEN_PIN  15
#define BLUE_PIN   16
#define BTN_START  27
#define SENSOR_PIN 34
#define READY_LED  2

long currentStep = 0;
const long totalSteps = 140608;
unsigned long lastFlashTime = 0;
bool ledState = false;

BluetoothSerial SerialBT;

struct DataPoint {
  uint8_t r;
  uint8_t g;
  uint8_t b;
  uint16_t val;
};

void setup() {
  Serial.begin(115200);

  Serial.println(F("--- PROJECT: Kinetic Eye ---"));
  Serial.print(F("FILE: ")); Serial.println(__FILE__);
  Serial.print(F("DATE: ")); Serial.println(__DATE__);
  Serial.print(F("TIME: ")); Serial.println(__TIME__);

  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  pinMode(BTN_START, INPUT_PULLUP);
  pinMode(READY_LED, OUTPUT);

  SerialBT.begin("Kinetic-Eye");
  Serial.println(F("STATUS: Ready."));
}

void runSpectralScan() {
  DataPoint point;
  uint8_t syncByte = 0xFF; // The "Anchor"

  for (int r = 0; r <= 250; r += 5) {
    for (int g = 0; g <= 250; g += 5) {
      for (int b = 0; b <= 250; b += 5) {
        analogWrite(RED_PIN, r);
        analogWrite(GREEN_PIN, g);
        analogWrite(BLUE_PIN, b);

        delayMicroseconds(20);

        currentStep++;
        int currentDelay = map(currentStep, 0, totalSteps, 500, 20);

        if (millis() - lastFlashTime >= currentDelay) {
          ledState = !ledState;
          digitalWrite(READY_LED, ledState);
          lastFlashTime = millis();
        }

        point.r = (uint8_t)r;
        point.g = (uint8_t)g;
        point.b = (uint8_t)b;
        point.val = (uint16_t)analogRead(SENSOR_PIN);

        // SEND SYNC BYTE THEN DATA
        SerialBT.write(syncByte);
        SerialBT.write((uint8_t*)&point, sizeof(point));
      }
    }
  }
}

void loop() {
  if (digitalRead(BTN_START) == LOW) {
    delay(50);
    if (digitalRead(BTN_START) == LOW) {
      runSpectralScan();
      while(digitalRead(BTN_START) == LOW);
    }
  }
}
