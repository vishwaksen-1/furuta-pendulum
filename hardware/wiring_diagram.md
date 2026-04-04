# Wiring Diagram

Full wiring reference for the Furuta Pendulum. See [`../docs/04_hardware_setup.md`](../docs/04_hardware_setup.md) for the complete setup procedure including current calibration.

---

## Pin Reference

### RPi Pico → A4988

| Pico Pin | GPIO | A4988 | Notes |
|----------|------|-------|-------|
| Pin 4 | GP2 | STEP | Step pulse |
| Pin 5 | GP3 | DIR | Direction |
| Pin 6 | GP4 | ENABLE | Active LOW |
| Pin 36 | 3V3 | VDD | Logic supply |
| Pin 36 | 3V3 | MS1 | Hard-wired HIGH |
| Pin 36 | 3V3 | MS2 | Hard-wired HIGH |
| Any GND | GND | MS3 | Hard-wired LOW → 1/8 step |
| Any GND | GND | GND | Common ground |

### RPi Pico → AS5600

| Pico Pin | GPIO | AS5600 | Notes |
|----------|------|--------|-------|
| Pin 11 | GP8 | SDA | I²C0, 4.7 kΩ pull-up |
| Pin 12 | GP9 | SCL | I²C0, 4.7 kΩ pull-up |
| Pin 36 | 3V3 | VCC | |
| Any GND | GND | GND | |

### A4988 → 17HS4401S Motor

| A4988 | Motor wire | Coil |
|-------|-----------|------|
| 1A | Black | A+ |
| 1B | Green | A− |
| 2A | Red | B+ |
| 2B | Blue | B− |

### Power

| From | To | Note |
|------|-----|------|
| 12V PSU (+) | A4988 VMOT | Through 100 µF cap to GND |
| 12V PSU (−) | A4988 GND, Pico GND | All grounds common |
| USB | Pico VSYS | Development power |

---

## Full Schematic

```
 12V ──┬──────────────────────────────────── VMOT (A4988)
       │
     [100µF 25V]    ← place physically close to A4988
       │
 GND ──┴──────────────────── A4988 GND ── Pico GND ── AS5600 GND

 RPi Pico                    A4988
 ┌──────────────┐            ┌───────────────────┐
 │ GP2  ────────┼────────────┤ STEP              │
 │ GP3  ────────┼────────────┤ DIR               │
 │ GP4  ────────┼────────────┤ ENABLE (act. LOW) │
 │ 3V3  ────────┼────────────┤ VDD               │
 │ 3V3  ────────┼────────────┤ MS1 (HIGH)        │ 1/8 step
 │ 3V3  ────────┼────────────┤ MS2 (HIGH)        │
 │ GND  ────────┼────────────┤ MS3 (LOW)         │
 │              │            │                   │
 │              │            │ 1A ──── BLK (A+)  │──► Motor
 │              │            │ 1B ──── GRN (A−)  │──► Motor
 │              │            │ 2A ──── RED (B+)  │──► Motor
 │              │            │ 2B ──── BLU (B−)  │──► Motor
 │              │            │ [Vref trimmer]    │
 │              │            │  set to 0.56V     │
 │              │            └───────────────────┘
 │ GP8 (SDA) ───┼──[4.7kΩ]──3V3
 │         └────┼────────────── SDA (AS5600)
 │ GP9 (SCL) ───┼──[4.7kΩ]──3V3
 │         └────┼────────────── SCL (AS5600)
 │ 3V3  ────────┼────────────── VCC (AS5600)
 │              │
 │ VSYS ────────┼────────────── USB
 └──────────────┘
```

---

## Important Notes

- The 100 µF capacitor **must** be placed physically close to the A4988 VMOT and GND pins. Motor deceleration generates back-EMF spikes that destroy the A4988 without this capacitor.
- Use 22 AWG or heavier wire for VMOT and GND power runs. Thin wire adds resistance that causes erratic motor behaviour under load.
- Keep I²C lines (SDA/SCL) physically away from the STEP pulse line. If they must cross, cross at 90°.
- AS5600 wires on the rotating arm: leave a **service loop** of slack at the pivot. Never route taut.
