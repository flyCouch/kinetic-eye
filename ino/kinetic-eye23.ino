/*
 * PROJECT: Kinetic Eye - Spectralmeter
 * FILE: kinetic-eye22.ino
 * DATE: 2026-04-18
 * HARDWARE: ESP32-CAM
 */

#include "BluetoothSerial.h"

// Header Pins
#define RED_PIN    14
#define GREEN_PIN  15
#define BLUE_PIN   2
#define BTN_START  4
#define SENSOR_PIN 13

BluetoothSerial SerialBT;

// Binary data structure (5 bytes total)
struct DataPoint {
  uint8_t r;
  uint8_t g;
  uint8_t b;
  uint16_t val;
};

void setup() {
  Serial.begin(115200);
  
  // Mandatory Project Header Prints
  Serial.println(F("--- PROJECT: Kinetic Eye ---"));
  Serial.print(F("FILE: ")); Serial.println(__FILE__);
  Serial.print(F("DATE: ")); Serial.println(__DATE__);
  Serial.print(F("TIME: ")); Serial.println(__TIME__);

  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  pinMode(BTN_START, INPUT_PULLUP);

  SerialBT.begin("Kinetic-Eye"); 
  Serial.println(F("STATUS: Binary Profiler Ready."));
}

void runSpectralScan() {
  // Notify worker of scan start
  SerialBT.write((uint8_t*)"START", 5); 

  DataPoint point;

  for (int r = 0; r <= 250; r += 5) {
    for (int g = 0; g <= 250; g += 5) {
      for (int b = 0; b <= 250; b += 5) {
        analogWrite(RED_PIN, r);
        analogWrite(GREEN_PIN, g);
        analogWrite(BLUE_PIN, b);
        
        delayMicroseconds(20);
        
        // Populate struct
        point.r = (uint8_t)r;
        point.g = (uint8_t)g;
        point.b = (uint8_t)b;
        point.val = (uint16_t)analogRead(SENSOR_PIN);
        
        // Write raw bytes
        SerialBT.write((uint8_t*)&point, sizeof(point));
      }
    }
  }

  // Notify worker of scan end
  SerialBT.write((uint8_t*)"END__", 5);

  // Reset LEDs
  analogWrite(RED_PIN, 0);
  analogWrite(GREEN_PIN, 0);
  analogWrite(BLUE_PIN, 0);
}

void loop() {
  if (digitalRead(BTN_START) == LOW) {
    delay(50); // Debounce
    runSpectralScan();
    while(digitalRead(BTN_START) == LOW) { delay(10); }
  }
}
