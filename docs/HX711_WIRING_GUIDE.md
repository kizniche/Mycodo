# HX711 Load Cell Bedrading - 50kg Half-Bridge

## Overzicht

Deze handleiding beschrijft de bedrading voor een **50kg Half-Bridge Load Cell** met een **HX711 ADC module** aangesloten op een **Raspberry Pi**.

## Componenten

| Component | Beschrijving |
|-----------|--------------|
| Load Cell | 50kg Half-Bridge (3 draden) |
| HX711 | 24-bit ADC module |
| Raspberry Pi | Model 3/4/5 |

---

## Bedrading Schema

```text
                    ┌─────────────────┐
                    │     HX711       │
                    │                 │
  LOAD CELL         │   E+  ◄────────── ROOD (Load Cell)
  (50kg Half-Bridge)│                 │
                    │   E-  ◄────────── ZWART (Load Cell)
                    │    │            │
                    │    └──────┐     │
                    │           │     │
                    │   A+  ◄───│───── GEEL (Load Cell)
                    │           │     │
                    │   A-  ◄───┘     │  ← BELANGRIJK: Kortsluit A- naar E-
                    │                 │
                    │   B+      (niet gebruikt)
                    │   B-      (niet gebruikt)
                    │                 │
                    │   VCC ◄──────────── 5V (Pi pin 2 of 4)
                    │   GND ◄──────────── GND (Pi pin 6, 9, 14, etc.)
                    │                 │
                    │   DT  ──────────►── GPIO 27 (Pi pin 13)
                    │   SCK ◄──────────── GPIO 21 (Pi pin 40)
                    │                 │
                    └─────────────────┘
```

---

## Stap-voor-Stap Bedrading

### 1. Load Cell naar HX711

| Load Cell Draad | Kleur  | HX711 Pin |
|-----------------|--------|-----------|
| Excitation+     | ROOD   | E+        |
| Excitation-     | ZWART  | E-        |
| Signal          | GEEL   | A+        |

**4-loadcell set (4x half-bridge) bedrading:**

- Alle **rode** draden samen op **E+**
- Alle **zwarte** draden samen op **E-**
- **Bovenste** sensor: gele/witte/groene draad op **A-**
- **Onderste** sensoren: gele/witte/groene draden samen op **A+**

### 2. Half-Bridge Fix (BELANGRIJK!)

**⚠️ Bij een half-bridge load cell MOET je A- verbinden met E-!**

Dit doe je door:

- Een kort draadje tussen A- en E- te solderen, OF
- Een jumper wire te gebruiken op het breadboard

```text
    E-  ●────────● A-
        └────────┘
         jumper
```

### 3. HX711 naar Raspberry Pi

| HX711 Pin | Raspberry Pi | Pin Nummer |
|-----------|--------------|------------|
| VCC       | 5V           | Pin 2 of 4 |
| GND       | GND          | Pin 6      |
| DT (DOUT) | GPIO 27      | Pin 13     |
| SCK       | GPIO 21      | Pin 40     |

---

## Raspberry Pi GPIO Pinout (Relevante Pins)

```text
                    3.3V  (1) (2)  5V  ◄── VCC
                   GPIO2  (3) (4)  5V
                   GPIO3  (5) (6)  GND ◄── GND
                   GPIO4  (7) (8)  GPIO14
                     GND  (9) (10) GPIO15
                  GPIO17 (11) (12) GPIO18
         DT ───► GPIO27 (13) (14) GND
                  GPIO22 (15) (16) GPIO23
                    3.3V (17) (18) GPIO24
                  GPIO10 (19) (20) GND
                   GPIO9 (21) (22) GPIO25
                  GPIO11 (23) (24) GPIO8
                     GND (25) (26) GPIO7
                   GPIO0 (27) (28) GPIO1
                   GPIO5 (29) (30) GND
                   GPIO6 (31) (32) GPIO12
                  GPIO13 (33) (34) GND
                  GPIO19 (35) (36) GPIO16
                  GPIO26 (37) (38) GPIO20
                     GND (39) (40) GPIO21 ◄── SCK
```

---

## Checklist voor Correcte Werking

- [ ] Load Cell ROOD → HX711 E+
- [ ] Load Cell ZWART → HX711 E-
- [ ] Load Cell WIT → HX711 A+
- [ ] **HX711 A- verbonden met E- (JUMPER!)**
- [ ] HX711 VCC → Pi 5V
- [ ] HX711 GND → Pi GND
- [ ] HX711 DT → Pi GPIO 27
- [ ] HX711 SCK → Pi GPIO 21

---

## Veelvoorkomende Problemen

### Probleem: Altijd 0 of -1 als waarde

**Oorzaak:** A- niet verbonden met E-  
**Oplossing:** Voeg jumper toe tussen A- en E-

### Probleem: Zeer instabiele waarden (spread > 1.000.000)

**Oorzaak:** Slechte verbindingen of 3.3V voeding  
**Oplossing:** Gebruik 5V voor VCC, controleer alle soldeerverbindingen

### Probleem: TIMEOUT errors

**Oorzaak:** DT/SCK draden verkeerd of niet aangesloten  
**Oplossing:** Controleer GPIO 27 (DT) en GPIO 21 (SCK)

### Probleem: Waarden veranderen niet bij druk

**Oorzaak:** Load cell niet correct aangesloten  
**Oplossing:** Controleer E+/E-/A+ bedrading

---

## Identificatie van draden (2 kΩ methode)

Bij veel 3-draads half-bridge load cells meet je **ongeveer 2 kΩ** tussen **ROOD** en **ZWART**. Dat zijn meestal **E+** en **E-**. De overgebleven draad (geel/wit/groen) is dan de **A draad (signaal)**.

---

## Voorbeeld set (AliExpress)

Als referentie kun je deze 4x half-bridge set gebruiken:

- [AliExpress 4x half-bridge set](https://nl.aliexpress.com/item/1005010026325539.html?spm=a2g0o.order_list.order_list_main.17.576579d252uTQf&gatewayAdapt=glo2nld)

---

## Test Command

Na correcte bedrading, test met:

```bash
sudo /opt/Mycodo/env/bin/python3 << 'EOF'
import RPi.GPIO as GPIO
import time

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

DT, SCK = 27, 21
GPIO.setup(SCK, GPIO.OUT)
GPIO.setup(DT, GPIO.IN)

def read():
    GPIO.output(SCK, False)
    while GPIO.input(DT): pass
    value = 0
    for _ in range(24):
        GPIO.output(SCK, True)
        GPIO.output(SCK, False)
        value = (value << 1) | GPIO.input(DT)
    GPIO.output(SCK, True)
    GPIO.output(SCK, False)
    return value - 0x1000000 if value & 0x800000 else value

GPIO.output(SCK, True)
time.sleep(0.1)
GPIO.output(SCK, False)
time.sleep(0.5)

print("5 metingen:")
for i in range(5):
    print(f"  {i+1}: {read():,}")
    time.sleep(0.2)

GPIO.cleanup()
EOF
```

---

## Specificaties

| Parameter | Waarde |
| --------- | ------ |
| Load Cell Capaciteit | 50 kg |
| Load Cell Type | Half-Bridge |
| ADC Resolutie | 24-bit |
| Sample Rate | 10 Hz (default) / 80 Hz |
| Voedingsspanning | 5V (aanbevolen) |
| GPIO Data | 27 |
| GPIO Clock | 21 |

---

*Document aangemaakt: 13 januari 2026*
*Project: Mycodo HX711 Input Module*
