/*
 * PROJECT: Kinetic Eye - Spectralmeter
 * MODULE: Progressive Progress Indicator
 * FILE: __FILE__
 * DATE: __DATE__
 * TIME: __TIME__
 */

#include "BluetoothSerial.h"

// ESP32 Dev-Kit Pin Assignments
#define RED_PIN    14
#define GREEN_PIN  15
#define BLUE_PIN   16
#define READY_LED  2   // Internal LED for status
#define BTN_START  27  // Stable boot pin
#define SENSOR_PIN 34  // Analog Input

BluetoothSerial SerialBT;

struct DataPoint {
  uint8_t r;
  uint8_t g;
  uint8_t b;
  uint16_t val;
};

unsigned long lastFlashTime = 0;
bool ledState = false;

void setup() {
  Serial.begin(115200);
  
  // Project Header Prints
  Serial.println(F("--- PROJECT: Kinetic Eye ---"));
  Serial.print(F("FILE: ")); Serial.println(__FILE__);
  Serial.print(F("DATE: ")); Serial.println(__DATE__);
  Serial.print(F("TIME: ")); Serial.println(__TIME__);

  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  pinMode(READY_LED, OUTPUT);
  pinMode(BTN_START, INPUT_PULLUP);

  // Indicate Readiness
  digitalWrite(READY_LED, HIGH); 

  SerialBT.begin("Kinetic-Eye"); 
  Serial.println(F("STATUS: Binary Profiler Ready."));
}

void runSpectralScan() {
  // Notify worker of scan start
  SerialBT.write((uint8_t*)"START", 5); 
  DataPoint point;

  // 52 steps per channel (0, 5, ... 255) = 52^3
  long totalSteps = 140608;
  long currentStep = 0;

  for (int r = 0; r <= 255; r += 5) {
    for (int g = 0; g <= 255; g += 5) {
      for (int b = 0; b <= 255; b += 5) {
        
        analogWrite(RED_PIN, r);
        analogWrite(GREEN_PIN, g);
        analogWrite(BLUE_PIN, b);
        
        delayMicroseconds(20);
        
        point.r = (uint8_t)r;
        point.g = (uint8_t)g;
        point.b = (uint8_t)b;
        point.val = (uint16_t)analogRead(SENSOR_PIN);
        
        SerialBT.write((uint8_t*)&point, sizeof(point));

        // Linear tempo increase based on scan progress
        currentStep++;
        int flashInterval = map(currentStep, 0, totalSteps, 300, 10);
        
        if (millis() - lastFlashTime >= flashInterval) {
          ledState = !ledState;
          digitalWrite(READY_LED, ledState);
          lastFlashTime = millis();
        }
      }
    }
  }

  // Finalize and reset status
  analogWrite(RED_PIN, 0);
  analogWrite(GREEN_PIN, 0);
  analogWrite(BLUE_PIN, 0);
  digitalWrite(READY_LED, HIGH); 
  SerialBT.write((uint8_t*)"END__", 5);
}

void loop() {
  if (digitalRead(BTN_START) == LOW) {
    delay(50); // Simple debounce
    runSpectralScan();
    // Wait for button release
    while(digitalRead(BTN_START) == LOW) { delay(10); }
  }
}
