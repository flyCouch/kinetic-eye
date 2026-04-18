/*
 * PROJECT: Kinetic Eye - Spectralmeter
 * FILE: kinetic-eye15.ino
 * DATE: 2026-04-18
 * HARDWARE: ESP32-CAM
 * NOTE: High-Resolution Scan (132,651 points)
 */

#include "BluetoothSerial.h"

// Header Pins
#define RED_PIN    14
#define GREEN_PIN  15
#define BLUE_PIN   16
#define BTN_START  12
#define SENSOR_PIN 13

BluetoothSerial SerialBT;

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
  Serial.println(F("STATUS: High-Res Profiler Ready."));
}

void runSpectralScan() {
  SerialBT.println(F("START_SCAN"));

  // RGB REFLECTANCE SWEEP (132,651 Points)
  for (int r = 0; r <= 250; r += 5) {
    for (int g = 0; g <= 250; g += 5) {
      for (int b = 0; b <= 250; b += 5) {
        analogWrite(RED_PIN, r);
        analogWrite(GREEN_PIN, g);
        analogWrite(BLUE_PIN, b);
        
        delay(1); 
        int val = analogRead(SENSOR_PIN);
        
        // Stream data
        SerialBT.print(r); SerialBT.print(F(","));
        SerialBT.print(g); SerialBT.print(F(","));
        SerialBT.print(b); SerialBT.print(F(","));
        SerialBT.println(val);
      }
    }
  }

  // Reset LEDs
  analogWrite(RED_PIN, 0);
  analogWrite(GREEN_PIN, 0);
  analogWrite(BLUE_PIN, 0);
  
  SerialBT.println(F("END_SCAN"));
}

void loop() {
  if (digitalRead(BTN_START) == LOW) {
    delay(50); // Debounce
    runSpectralScan();
    while(digitalRead(BTN_START) == LOW) { delay(10); }
  }
}
