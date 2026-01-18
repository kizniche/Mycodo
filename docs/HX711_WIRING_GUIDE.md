# HX711 Load Cell Wiring - 50 kg Half-Bridge

## Overview

This guide covers wiring a **50 kg half-bridge load cell** to an **HX711 ADC module** connected to a **Raspberry Pi**.

## Components

| Component | Description |
| --------- | ----------- |
| Load cell | 50 kg half-bridge (3 wires) |
| HX711 | 24-bit ADC module |
| Raspberry Pi | Model 3/4/5 |

---

## Wiring Diagram

### 4x half-bridge load cells (bathroom-scale style)

```text
    ┌─────────────────┐
    │     HX711       │
    │                 │
  RED (all)   ─────────────► │   E+
  BLACK (all) ─────────────► │   E-
  TOP sensor signal ───────► │   A-
  BOTTOM sensor signals ───► │   A+
    │                 │
    │   B+      (not used)
    │   B-      (not used)
    │                 │
    │   VCC ◄──────────── 5V (Pi pin 2 or 4)
    │   GND ◄──────────── GND (Pi pin 6, 9, 14, etc.)
    │                 │
    │   DT  ──────────►── GPIO 27 (Pi pin 13)
    │   SCK ◄──────────── GPIO 21 (Pi pin 40)
    │                 │
    └─────────────────┘
```

---

## Step-by-Step Wiring

### 1. Load Cell to HX711

| Load cell wire | Color | HX711 pin |
| ------------- | ----- | --------- |
| Excitation+ | RED | E+ |
| Excitation- | BLACK | E- |
| Signal | YELLOW | A+ |

**4-loadcell set (4x half-bridge) wiring:**

- All **red** wires together to **E+**
- All **black** wires together to **E-**
- **Top** sensor signal (yellow/white/green) to **A-**
- **Bottom** sensors signal wires (yellow/white/green) together to **A+**

### 2. Half-Bridge Fix (IMPORTANT)

**⚠️ Do NOT short A- to E- when using a 4-loadcell set.**

Do this by:

- Soldering a short wire between A- and E-, OR
- Using a jumper wire on a breadboard

```text
  E-  ●────────● A-
    └────────┘
     jumper
```

### 3. HX711 to Raspberry Pi

| HX711 pin | Raspberry Pi | Pin number |
| --------- | ------------ | ---------- |
| VCC | 5V | Pin 2 or 4 |
| GND | GND | Pin 6 |
| DT (DOUT) | GPIO 27 | Pin 13 |
| SCK | GPIO 21 | Pin 40 |

---

## Raspberry Pi GPIO Pinout (Relevant Pins)

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

## Checklist

- [ ] Load cell RED → HX711 E+
- [ ] Load cell BLACK → HX711 E-
- [ ] Load cell signal (yellow/white/green) → HX711 A+
- [ ] **HX711 A- shorted to E- (jumper)**
- [ ] HX711 VCC → Pi 5V
- [ ] HX711 GND → Pi GND
- [ ] HX711 DT → Pi GPIO 27
- [ ] HX711 SCK → Pi GPIO 21

---

## Troubleshooting

### Issue: Always 0 or -1

**Cause:** A- is not connected to E-  
**Fix:** Add a jumper between A- and E-

### Issue: Very unstable values (spread > 1,000,000)

**Cause:** Poor connections or 3.3V supply  
**Fix:** Use 5V for VCC and check solder joints

### Issue: TIMEOUT errors

**Cause:** DT/SCK wiring is incorrect or disconnected  
**Fix:** Verify GPIO 27 (DT) and GPIO 21 (SCK)

### Issue: Values do not change with pressure

**Cause:** Load cell wiring incorrect  
**Fix:** Check E+/E-/A+ wiring

---

## Wire Identification (2 kΩ Method)

Many 3-wire half-bridge load cells measure **about 2 kΩ** between **RED** and **BLACK**. These are typically **E+** and **E-**. The remaining wire (yellow/white/green) is the **signal (A) wire**.

---

## Example Set (AliExpress)

As a reference, this 4x half-bridge set is commonly used:

- [AliExpress 4x half-bridge set](https://nl.aliexpress.com/item/1005010026325539.html?spm=a2g0o.order_list.order_list_main.17.576579d252uTQf&gatewayAdapt=glo2nld)

---

## Test Command

After wiring, test with:

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
  while GPIO.input(DT):
    pass
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

print("5 samples:")
for i in range(5):
  print(f"  {i+1}: {read():,}")
  time.sleep(0.2)

GPIO.cleanup()
EOF
```

---

## Specifications

| Parameter | Value |
| --------- | ----- |
| Load cell capacity | 50 kg |
| Load cell type | Half-bridge |
| ADC resolution | 24-bit |
| Sample rate | 10 Hz (default) / 80 Hz |
| Supply voltage | 5V (recommended) |
| GPIO data | 27 |
| GPIO clock | 21 |

---

*Document created: 13 January 2026*  
*Project: Mycodo HX711 Input Module*
