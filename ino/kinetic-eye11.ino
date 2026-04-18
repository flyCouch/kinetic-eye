/*
 * PROJECT: Kinetic Eye - Spectralmeter
 * FILE: KineticEye_Worker 10
 * DATE: April 17, 2026
 * HARDWARE: ESP32-CAM (Damaged Camera Repurposed)
 * SENSOR: Single Light Module on GPIO 13
 */

#include "BluetoothSerial.h"

// Header Pins (Standard ESP32-CAM Layout)
#define RED_PIN    14
#define GREEN_PIN  15
#define BLUE_PIN   16
#define BTN_START  12
#define SENSOR_PIN 13

BluetoothSerial SerialBT;

void setup() {t
  Serial.begin(115200);
  
  // Mandatory Project Header Print (Flash Optimized)
  Serial.println(F("--- PROJECT: Kinetic Eye ---"));
  Serial.print(F("FILE: ")); Serial.println(__FILE__);
  Serial.print(F("DATE: ")); Serial.println(__DATE__);
  Serial.print(F("TIME: ")); Serial.println(__TIME__);

  pinMode(RED_PIN, OUTPUT);
  pinMode(GREEN_PIN, OUTPUT);
  pinMode(BLUE_PIN, OUTPUT);
  pinMode(BTN_START, INPUT_PULLUP);

  // Initialize Bluetooth
  SerialBT.begin("Kinetic-Eye"); 
  Serial.println(F("Connect and press Scanner Button."));
}

void runSpectralScan() {
  
  // 1. THE RGB REFLECTANCE SWEEP (17,576 Points)
  for (int r = 0; r <= 250; r += 10) {
    for (int g = 0; g <= 250; g += 10) {
      for (int b = 0; b <= 250; b += 10) {
        analogWrite(RED_PIN, r);
        analogWrite(GREEN_PIN, g);
        analogWrite(BLUE_PIN, b);
        
        // Let the light stabilize and the ADC clear noise
        delay(7); 

        int val = analogRead(SENSOR_PIN);
        
        // Instant stream: R,G,B,Reflectance
        SerialBT.print(r); SerialBT.print(F(","));
        SerialBT.print(g); SerialBT.print(F(","));
        SerialBT.print(b); SerialBT.print(F(","));
        SerialBT.println(val);
      }
    }
  }

  // Kill visible light
  analogWrite(RED_PIN, 0);
  analogWrite(GREEN_PIN, 0);
  analogWrite(BLUE_PIN, 0);
  delay(200);
  }
  
  // Signal phone to Beep, Vibrate, and save the file
  SerialBT.println(F("END_SCAN"));
}

void loop() {
  // Wait for the worker to trigger the scan
  if (digitalRead(BTN_START) == LOW) {
    delay(50); // Debounce
    runSpectralScan();
    
    // Prevent multiple triggers from one press
    while(digitalRead(BTN_START) == LOW) {
      delay(10);
    }
  }
}
