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

### 2. A- to E- Short (IMPORTANT)

**⚠️ Do NOT short A- to E- when using a 4-loadcell set.**

This guide only covers the 4x half-bridge set. If you are wiring a single half-bridge load cell, use a dedicated single-sensor wiring guide.

### 3. HX711 to Raspberry Pi

| HX711 pin | Raspberry Pi | Pin number |
| --------- | ------------ | ---------- |
| VCC | 5V | Pin 2 or 4 |
| GND | GND | Pin 6 |
| DT (DOUT) | GPIO 27 | Pin 13 |
| SCK | GPIO 21 | Pin 40 |

---

## Checklist

- [ ] Load cell RED → HX711 E+
- [ ] Load cell BLACK → HX711 E-
- [ ] Load cell signal (yellow/white/green) → HX711 A+
- [ ] HX711 VCC → Pi 5V
- [ ] HX711 GND → Pi GND
- [ ] HX711 DT → Pi GPIO 27
- [ ] HX711 SCK → Pi GPIO 21

---

## Troubleshooting

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

## How a Load Cell Works

A load cell is a set of strain gauges wired as a half-bridge. When force is applied, the resistance changes slightly. The HX711 measures this tiny differential change and outputs a digital value. The value is not in grams until you apply a calibration factor.

---

## How to Measure and Verify

### With a multimeter (wiring check)

1. Measure resistance between **RED** and **BLACK** on each sensor. It should be around **2 kΩ**.
2. The third wire (yellow/white/green) is the **signal** for that sensor.
3. Verify all RED wires are tied to **E+** and all BLACK wires to **E-**.

### With software (signal check)

1. In Mycodo, add the HX711 input with the same GPIO pins as wired.
2. Watch raw values with no load. They should be stable.
3. Place a known weight and confirm the raw value shifts consistently.
4. Use the calibration factor to convert raw values to grams.

For advanced testing and calibration runs, use the HX711 test tool in [mycodo/scripts/hx711_test.py](mycodo/scripts/hx711_test.py).

---

## Example Set (AliExpress)

As a reference, this 4x half-bridge set is commonly used:

- [AliExpress 4x half-bridge set](https://nl.aliexpress.com/item/1005010026325539.html?spm=a2g0o.order_list.order_list_main.17.576579d252uTQf&gatewayAdapt=glo2nld)

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
