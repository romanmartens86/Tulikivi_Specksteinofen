#include <Arduino.h>
#include "max6675.h"

// ==========================================
// Pin-Definitionen für ESP32 DevKitC V4
// ==========================================
const int PIN_SCK  = 18;  // Gemeinsamer SPI-Takt (SCK / CLK)
const int PIN_MISO = 19;  // Gemeinsame SPI-Datenleitung (SO / DO)

const int PIN_CS1  = 5;   // Chip Select Sensor 1: Rauchrohr
const int PIN_CS2  = 4;   // Chip Select Sensor 2: Speckstein

const int PIN_LED  = 2;   // Onboard blaue LED (GPIO 2)

// Initialisierung der MAX6675 Sensoren
MAX6675 sensorRauchrohr(PIN_SCK, PIN_CS1, PIN_MISO);
MAX6675 sensorSpeckstein(PIN_SCK, PIN_CS2, PIN_MISO);

// Hilfsfunktion: Rohe 16-Bit-Daten vom MAX6675 auslesen (für präzise Diagnose)
uint16_t readRawMAX6675(int csPin, int sckPin, int misoPin) {
  uint16_t d = 0;
  digitalWrite(csPin, LOW);
  delayMicroseconds(10);

  for (int i = 15; i >= 0; i--) {
    digitalWrite(sckPin, LOW);
    delayMicroseconds(10);
    if (digitalRead(misoPin)) {
      d |= (1 << i);
    }
    digitalWrite(sckPin, HIGH);
    delayMicroseconds(10);
  }

  digitalWrite(csPin, HIGH);
  return d;
}

void printSensorStatus(const char* name, int csPin, MAX6675& sensor) {
  uint16_t raw = readRawMAX6675(csPin, PIN_SCK, PIN_MISO);
  delay(10); // Kleiner Abstand zwischen den Messungen
  float tempC = sensor.readCelsius();

  Serial.printf("[%-18s] ", name);

  // Diagnose anhand des Rohwerts
  if (raw == 0x0000) {
    Serial.printf("FEHLER: Rohwert 0x0000 -> Keine Daten! Prüfe VCC (3.3V), GND oder MISO (GPIO 19)\n");
  } else if (raw == 0xFFFF) {
    Serial.printf("FEHLER: Rohwert 0xFFFF -> MISO dauerhaft HIGH! Prüfe Verdrahtung oder CS (GPIO %d)\n", csPin);
  } else if (raw & 0x0004) {
    Serial.printf("WARNUNG: Fühler getrennt! (Bit D2=1). Bitte Thermoelement-Drähte an den Schraubklemmen festziehen.\n");
  } else if (isnan(tempC)) {
    Serial.printf("FEHLER: Sensor liefert NaN!\n");
  } else {
    Serial.printf("STATUS: OK | Temperatur: %6.2f °C | Raw: 0x%04X\n", tempC, raw);
  }
}

void setup() {
  Serial.begin(115200);
  delay(1000); // Warten auf Serial Monitor

  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  Serial.println("\n=======================================================");
  Serial.println("  🪵 Tulikivi Specksteinofen - MAX6675 Sensor-Diagnose");
  Serial.println("=======================================================");
  Serial.printf("  SPI SCK  (Takt):       GPIO %d\n", PIN_SCK);
  Serial.printf("  SPI MISO (Daten/SO):   GPIO %d\n", PIN_MISO);
  Serial.printf("  CS Sensor 1 (Rauchrohr):  GPIO %d\n", PIN_CS1);
  Serial.printf("  CS Sensor 2 (Speckstein): GPIO %d\n", PIN_CS2);
  Serial.println("=======================================================\n");

  // MAX6675 benötigt nach dem Einschalten mindestens 250ms für die erste Konvertierung
  delay(500);
}

void loop() {
  digitalWrite(PIN_LED, HIGH);

  Serial.println("--- Messung ---");
  printSensorStatus("1. Rauchrohr", PIN_CS1, sensorRauchrohr);
  delay(100);
  printSensorStatus("2. Speckstein", PIN_CS2, sensorSpeckstein);
  Serial.println();

  digitalWrite(PIN_LED, LOW);
  delay(1000); // 1 Sekunde Pause bis zur nächsten Messung
}
