/*
 * PROJECT: Kinetic Eye - Spectral Reflectance Profiler
 * FILE: kinetic-eye9.ino
 * DATE: 2026-04-18
 * HARDWARE: ESP32-CAM
 */

#include "BluetoothSerial.h"

// Header Pins
#define RED_PIN    25
#define GREEN_PIN  26
#define BLUE_PIN   27
#define BTN_START  12
#define SENSOR_PIN 13

BluetoothSerial SerialBT;

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

  SerialBT.begin("KineticEye_Profiler"); 
  Serial.println(F("STATUS: Profiler Ready."));
}

void runSpectralScan() {
  SerialBT.println(F("START_SCAN"));

  // RGB REFLECTANCE SWEEP
  // This generates the plant's unique reflectance fingerprint
  for (int r = 0; r <= 250; r += 25) { // Increments adjusted for speed
    for (int g = 0; g <= 250; g += 25) {
      for (int b = 0; b <= 250; b += 25) {
        analogWrite(RED_PIN, r);
        analogWrite(GREEN_PIN, g);
        analogWrite(BLUE_PIN, b);
        
        delay(10); // Short stabilization
        int val = analogRead(SENSOR_PIN);
        
        // Output format for Termux parsing: R,G,B,Intensity
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
