# Hardware Setup

## 1. Component List

| Component | Part Number | Qty | Notes |
|-----------|-------------|-----|-------|
| Microcontroller | Raspberry Pi Pico | 1 | RP2040, MicroPython |
| Stepper motor | 17HS4401S NEMA 17 | 1 | 1.0 A/phase, 0.44 N·m, 1.8°/step |
| Motor driver | A4988 breakout | 1 | Verify sense resistor value |
| Angle encoder | AS5600 breakout | 1 | 12-bit magnetic, I²C |
| Magnet | 6 mm diametric disc | 1 | Neodymium, for AS5600 |
| Power supply | 12V DC, ≥ 2A | 1 | For motor rail |
| Decoupling cap | 100 µF 25V electrolytic | 1 | **Critical** — VMOT protection |
| Pull-up resistors | 4.7 kΩ | 2 | I²C SDA + SCL lines |
| Wiring | 22 AWG stranded | — | Use for VMOT/GND; 26 AWG for signals |

---

## 2. A4988 Current Calibration — Do This Before Connecting the Motor

**This is the most critical setup step.** Incorrect current causes either motor stall (too low) or motor overheating and driver destruction (too high).

### Formula

$$V_{ref} = I_{limit} \times 8 \times R_s$$

Where R_s is the current sense resistor on the A4988 board. Most breakout boards use **R_s = 0.100 Ω**. Verify by reading the resistor markings near the motor output pins:
- Marked **R100** → 0.100 Ω
- Marked **R050** → 0.050 Ω

### Target current

The 17HS4401S is rated at 1.0 A/phase. We run at **70% = 0.7 A** for a balance between torque and heat.

```
Vref = 0.7 × 8 × 0.100 = 0.56 V    (for R_s = 0.100 Ω)
Vref = 0.7 × 8 × 0.050 = 0.28 V    (for R_s = 0.050 Ω)
```

### Calibration Procedure

1. **Motor disconnected.** Do not connect motor during calibration.
2. Apply 12 V to VMOT and GND on A4988.
3. Apply 3.3 V to VDD and GND on A4988 (from Pico or bench supply).
4. Do not send any STEP pulses.
5. Place multimeter probes: **red on trimmer wiper centre**, **black on GND**.
6. Adjust trimmer until reading matches target Vref.
7. Connect motor after calibration is confirmed.

> ⚠️ The Vref shifts when the motor is connected. Always calibrate motor-disconnected, then connect the motor.

---

## 3. Pin Connections

### A4988 ↔ RPi Pico

| Signal | Pico GPIO | A4988 Pin | Notes |
|--------|-----------|-----------|-------|
| STEP | GP2 | STEP | One pulse = one microstep |
| DIR | GP3 | DIR | HIGH = CW, LOW = CCW |
| ENABLE | GP4 | ENABLE | **Active LOW** — drive LOW to enable |
| MS1 | — | MS1 | Tie to 3.3V (HIGH) |
| MS2 | — | MS2 | Tie to 3.3V (HIGH) |
| MS3 | — | MS3 | Tie to GND (LOW) |
| VDD | 3V3 (pin 36) | VDD | A4988 logic supply (3.0–5.5V) |
| GND | GND | GND | Common ground — critical |

MS1/MS2/MS3 are hard-wired for **1/8 microstepping** (1600 steps/rev). No GPIO needed.

**Microstepping truth table:**

| MS1 | MS2 | MS3 | Mode |
|-----|-----|-----|------|
| L | L | L | Full step |
| H | L | L | 1/2 step |
| L | H | L | 1/4 step |
| **H** | **H** | **L** | **1/8 step ← use this** |
| H | H | H | 1/16 step |

### AS5600 ↔ RPi Pico

| Signal | Pico GPIO | AS5600 Pin | Notes |
|--------|-----------|------------|-------|
| SDA | GP8 | SDA | I²C0 data — add 4.7 kΩ pull-up to 3.3V |
| SCL | GP9 | SCL | I²C0 clock — add 4.7 kΩ pull-up to 3.3V |
| VCC | 3V3 (pin 36) | VCC | |
| GND | GND | GND | |

> Most AS5600 breakout boards include onboard pull-ups. Verify before adding external ones — double pull-ups are fine but if the board has 2.2 kΩ, you do not need to add 4.7 kΩ.

### 17HS4401S Motor ↔ A4988

| Motor wire | Coil | A4988 pin |
|------------|------|-----------|
| Black | A+ | 1A |
| Green | A− | 1B |
| Red | B+ | 2A |
| Blue | B− | 2B |

> If the motor spins in the wrong direction, swap either the A pair (Black ↔ Green) **or** the B pair (Red ↔ Blue) — not both simultaneously.

---

## 4. Full Wiring Schematic

```
╔═══════════════════════════════════════════════════════════════╗
║  POWER                                                        ║
║  12V PSU (+) ──────────────────────┬─────── VMOT (A4988)     ║
║                                  [100µF]                      ║
║  12V PSU (−) / GND ────────────────┴─────── GND  (A4988)     ║
║                    └──────────────────────── GND  (Pico)      ║
║                    └──────────────────────── GND  (AS5600)    ║
╠═══════════════════════════════════════════════════════════════╣
║  PICO ↔ A4988                                                 ║
║  GP2  ──────────────────────────────────── STEP               ║
║  GP3  ──────────────────────────────────── DIR                ║
║  GP4  ──────────────────────────────────── ENABLE (active LOW)║
║  3V3  ──────────────────────────────────── VDD                ║
║  3V3  ──────────────────────────────────── MS1                ║
║  3V3  ──────────────────────────────────── MS2                ║
║  GND  ──────────────────────────────────── MS3                ║
╠═══════════════════════════════════════════════════════════════╣
║  PICO ↔ AS5600                                                ║
║  GP8  ──[4.7kΩ→3V3]────────────────────── SDA                ║
║  GP9  ──[4.7kΩ→3V3]────────────────────── SCL                ║
║  3V3  ──────────────────────────────────── VCC                ║
╠═══════════════════════════════════════════════════════════════╣
║  A4988 ↔ MOTOR                                                ║
║  1A ─── Black (A+)     2A ─── Red  (B+)                      ║
║  1B ─── Green (A−)     2B ─── Blue (B−)                      ║
╠═══════════════════════════════════════════════════════════════╣
║  PICO POWER                                                   ║
║  VSYS (pin 39) ─── USB during development                     ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 5. AS5600 Magnet Installation

- Use a **6 mm diametrically magnetised disc magnet** (neodymium).
- Mount magnet **on the pendulum pivot shaft**, centred on the AS5600 chip axis.
- Air gap: **0.5–3 mm** (verify with MD bit in status register — see `test_encoder.py`).
- The magnet rotates **with the pendulum**; the AS5600 PCB is **fixed** to the arm.
- Centre the magnet carefully — off-centre mounting causes angle-dependent error.

---

## 6. Physical Assembly Order

1. Mount stepper motor to base plate.
2. Attach arm to motor shaft. Tighten set screw — any shaft slop corrupts step count.
3. Mount pendulum pivot bearing at arm tip.
4. Thread AS5600 wires through or along the arm **before** attaching pendulum rod.
5. Attach pendulum rod to pivot.
6. Glue or press-fit magnet onto pendulum pivot shaft, centred and flush.
7. Mount AS5600 PCB on arm, facing magnet, ~1–2 mm gap.
8. Leave a **service loop** of slack wire at the pivot — do not run wires taut.
9. Mount Pico and A4988 on the fixed base (they do not rotate).
10. Add JST connector at arm-base wire junction for easy disassembly.
11. Install 100 µF capacitor close to A4988 VMOT/GND pins.

---

## 7. Pre-Power Checklist

- [ ] Vref set to 0.56 V (motor disconnected during measurement)
- [ ] Motor connected to A4988 after calibration
- [ ] 100 µF cap across VMOT/GND, physically close to A4988
- [ ] All grounds common (Pico GND, A4988 GND, 12V PSU GND)
- [ ] AS5600 pull-ups present on SDA and SCL
- [ ] Magnet centred, MD status bit = 1 (verified in software test)
- [ ] MS1 = H, MS2 = H, MS3 = L (1/8 step confirmed)
- [ ] ENABLE pin wired and LOW = enable understood in firmware
- [ ] Wire service loop present at pivot, no taut wires
