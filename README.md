# 🪵 Tulikivi Specksteinofen Dashboard & Überwachung für Home Assistant

Intelligente Überwachung und Visualisierung für einen **Tulikivi Specksteinofen (ca. 1.000 kg Speichermasse)** mit einem **ESP32** und zwei **MAX6675 Thermoelement-Sensoren**.

---

## 🌟 Hauptfunktionen

- 🔥 **Rauchrohr-Echtzeitüberwachung:** Erkennt sekundenschnell das Anzünden, den Vollbrand und das Verlöschen des Feuers.
- 🧱 **Speckstein-Speicherladung (0–100%):** Misst die verzögerte Wärmeaufnahme des Steins (Höhepunkt nach 4–6 Stunden).
- ⚡ **Echte Energieberechnung (in kWh):** Berechnet die thermisch gespeicherte Energie anhand der 1.000 kg Specksteinmasse ($Q = m \cdot c \cdot \Delta T$).
- 🧠 **Selbstlernende 100%-Kalibrierung:** Der Peak-Detektor merkt sich nach dem ersten Abbrand automatisch den Maximalwert des Steins und passt die 100%-Skala dynamisch an.
- 🔔 **Intelligenter Klappen-Alarm (Glutphase):** Schickt eine Benachrichtigung aufs Smartphone, sobald die Flammen erloschen sind und nur noch Glut da ist: **„Luftklappe JETZT schließen!“** (verhindert, dass die gespeicherte Wärme durch den Schornstein abgesaugt wird).
- ⏳ **Restwärme-Prognose:** Schätzt ab, wie viele Stunden der Ofen noch spürbar Wärme an den Wohnraum abgibt.
- 📊 **Fertiges Lovelace Dashboard:** Wunderschöne Balken, Tachos, Kurven und Status-Badges für Home Assistant.

---

## 🔌 Hardware & Pinbelegung

Verwendet wird ein **ESP32 DevKitC V4** mit **zwei MAX6675-Modulen**:

| MAX6675 Pin | Sensor 1: Rauchrohr | Sensor 2: Speckstein Außen | ESP32 DevKitC V4 Pin |
|:---|:---|:---|:---|
| **VCC** | VCC | VCC | **3V3** *(gemeinsam)* |
| **GND** | GND | GND | **GND** *(gemeinsam)* |
| **SCK** *(Clock)* | SCK | SCK | **GPIO 18** *(gemeinsam)* |
| **SO** *(Data Out)*| SO | SO | **GPIO 19** *(gemeinsam)* |
| **CS** *(Chip Select)* | **CS** | — | **GPIO 5** *(nur Sensor 1)* |
| **CS** *(Chip Select)* | — | **CS** | **GPIO 4** *(nur Sensor 2)* |

---

## 🚀 Schritt-für-Schritt Installation

### Schritt 1: ESP32 mit ESPHome flashen
1. Öffne die Datei [`esphome/specksteinofen.yaml`](esphome/specksteinofen.yaml).
2. Trage dein WLAN (`ssid` und `password`) ein.
3. Flashen:
   - Entweder über das **ESPHome Add-On** in Home Assistant (Neues Gerät ➔ Code einfügen ➔ Installieren).
   - Oder direkt am PC per USB über [web.esphome.io](https://web.esphome.io).
4. Sobald der ESP32 im WLAN ist, erkennt Home Assistant das Gerät automatisch als **„Tulikivi Specksteinofen“** mit den beiden Entitäten:
   - `sensor.tulikivi_specksteinofen_rauchrohr_temperatur`
   - `sensor.tulikivi_specksteinofen_speckstein_temperatur`

---

### Schritt 2: Installation in Home Assistant

#### Option A: Über HACS (Empfohlen)
Da diese Integration als HACS-fähige Custom Integration aufgebaut ist, kannst du sie direkt über HACS hinzufügen:

1. Öffne in Home Assistant **HACS**.
2. Klicke oben rechts auf die **drei Punkte** (Menü) ➔ **Benutzerdefinierte Repositories** (*Custom repositories*).
3. Trage folgende Daten ein:
   - **Repository:** `https://github.com/romanmartens86/Tulikivi_Specksteinofen`
   - **Typ / Kategorie:** `Integration`
4. Klicke auf **Hinzufügen**.
5. Suche nach **Tulikivi Specksteinofen**, klicke auf **Herunterladen** und starte Home Assistant neu.
6. Gehe in Home Assistant auf **Einstellungen ➔ Geräte & Dienste ➔ Integration hinzufügen** und wähle **„Tulikivi Specksteinofen“**.
   - Dort öffnet sich ein Einrichtungsassistent: Du wählst einfach deine beiden Sensoren aus und gibst das Gewicht (z.B. `1000` oder `2600` kg) ein!

*(Hinweis: Damit HACS ohne GitHub-Token darauf zugreifen kann, muss das GitHub-Repository öffentlich (public) sein. Alternativ kann man den Ordner `custom_components/tulikivi_specksteinofen` einfach manuell in den `config/`-Ordner kopieren).*

---

#### Option B: Manuell über Package (Alternative ohne HACS)
Das mitgelieferte YAML-Package bündelt alle mathematischen Berechnungen, Sensoren, Schalter und Automationen in einer Datei.

1. Stelle sicher, dass in deiner Home Assistant `configuration.yaml` Packages aktiviert sind:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
2. Kopiere die Datei [`homeassistant/packages/specksteinofen.yaml`](homeassistant/packages/specksteinofen.yaml) in deinen Home Assistant Ordner `config/packages/`.
3. Gehe in Home Assistant auf **Entwicklerwerkzeuge ➔ YAML ➔ „YAML-Konfiguration neu laden“**.

---

### Schritt 3: Dashboard-Karte hinzufügen
1. Öffne dein Home Assistant Dashboard.
2. Klicke oben rechts auf **Bearbeiten ➔ Karte hinzufügen ➔ Manuell (Code)**.
3. Kopiere den gesamten Inhalt aus [`homeassistant/dashboard/specksteinofen_ui.yaml`](homeassistant/dashboard/specksteinofen_ui.yaml) hinein und klicke auf **Speichern**.

---

## 🧮 Physikalische Berechnung

Speckstein hat eine spezifische Wärmekapazität von $c \approx 0{,}98\text{ kJ}/(\text{kg}\cdot\text{K}) \approx 0{,}272\text{ Wh}/(\text{kg}\cdot\text{K})$.

Bei einer Ofenmasse von **1.000 kg**:
$$Q = 1000\text{ kg} \times 0{,}0002722 \times (T_{\text{Stein}} - T_{\text{Raum}})$$

- **Beispiel 1 (1.000 kg Ofen):**  
  $\Delta T = 50\text{ K}$ (von 20 °C auf 70 °C)  
  $$Q = 1000 \times 0{,}0002722 \times 50 \approx \mathbf{13{,}6\text{ kWh}}$$
- **Beispiel 2 (großer 2.600 kg Speicherofen):**  
  $\Delta T = 50\text{ K}$ (von 20 °C auf 70 °C)  
  $$Q = 2600 \times 0{,}0002722 \times 50 \approx \mathbf{35{,}4\text{ kWh}}$$

---

## ⚙️ Ofen-Konfiguration im Dashboard (Gewicht & Lernmodus)

Direkt auf der Dashboard-Karte oder über Home Assistant Entitäten kannst du folgende Parameter ganz einfach per Eingabefeld einstellen:
- **Speichermasse (kg):** Flexibel von **200 kg bis 5.000 kg** (z.B. `1000` oder `2600` eintippen).
  - *Die Berechnung der gespeicherten kWh, der maximalen Kapazität und der Abkühlzeit passt sich automatisch an das eingegebene Gewicht an!*
- **Raumtemperatur (0% Grenze):** Standard 20 °C.
- **100% Temperatur-Grenze (Gelernt):** Standard 70 °C.
- **Automatisches Anlernen (Schalter):** Registriert nach dem ersten Vollbrand automatisch den Höchstwert deines Ofens und passt die 100%-Marke an.
