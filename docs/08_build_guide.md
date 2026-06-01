# Build Your Own Furuta Pendulum — Under ₹4000

**Status**: Production validated (tested and working at IIT Kharagpur Design Lab)

**Total Cost**: ~₹3600 (breakup below)

**Build Time**: 4-6 hours (3D printing ~12 hours, electronics assembly ~2 hours)

---

## Bill of Materials (BOM)

| Component | Part Number/Source | Cost (₹) | Notes |
|-----------|-------------------|----------|-------|
| **3D Printed Parts** | Custom STL files | ~900 | Includes arm, pendulum bob, brackets. See `hardware/stl/` |
| **Microcontroller** | Raspberry Pi Pico | ~400 | Official Pi Foundation |
| **Stepper Motor** | NEMA 17 (17HS4401S) | ~600 | 1.7A, ~0.4 Nm holding torque |
| **Motor Driver** | A4988 | ~100 | Allegro, 16-microstep capable |
| **Angle Sensor** | AS5600 (12-bit I²C) | ~100 | Absolute magnetic encoder |
| **Power Supply** | 12V AC-DC Adapter (1A) | ~200 | Regulated, ≥1A recommended |
| **Cables & USB** | USB-C data cable + jumpers | ~300 | For Pico programming & data |
| **Misc** | Breadboard, wires, tape, fasteners | ~1000 | Prototyping components, wastage buffer |
| **TOTAL** | | **~₹3600** | Excludes shipping |

---

## Why ₹3600 vs ₹8,00,000 Commercial?

| Feature | DIY | Commercial |
|---------|-----|-----------|
| **Complexity** | Simplified (balance-only) | Full swing-up, multiple modes |
| **Integration** | Off-the-shelf components | Custom PCBs, encoders |
| **Precision** | Sufficient for education | Research-grade (~5x cost) |
| **Customization** | Fully open, modifiable | Locked firmware |
| **Learning curve** | Part of the experience | Plug-and-play |

---

## Part-by-Part Guide

### 1. Raspberry Pi Pico (~₹400)

**What it is**: Microcontroller running MicroPython

**Why it**: 
- Affordable
- MicroPython support (faster to code than C)
- Dual-core 133 MHz processor (plenty for 500 Hz control loop)
- Built-in USB for easy flashing

**Where to buy**: 
- Robocraze, IndiaStack, Amazon India

**Alternatives**:
- Arduino Uno (₹300-400, but slower, requires C code)
- ESP32 (₹250-300, but power consumption higher for continuous operation)

---

### 2. NEMA 17 Stepper Motor (~₹600)

**What it is**: Closed-loop stepper for precise positioning (no feedback needed from motor itself)

**Why it**: 
- 1600 steps/rev × 8-microstep = 12,800 pulses/rev
- High resolution arm rotation
- Holding torque sufficient for our geometry
- Cheap, robust, open-source drivers available

**Specs to verify**:
- Voltage: 12V nominal
- Current: 1.7A per coil (we set current limit on A4988)
- Holding torque: ≥0.4 Nm

**Where to buy**: 
- Robocraze, Adafruit (if importing), AliExpress (longer lead time)

**Installation**:
- Mount via coupling to arm rotational axis
- Ensure no mechanical binding

---

### 3. A4988 Stepper Driver (~₹100)

**What it is**: Microstepping driver for NEMA 17

**Why it**: 
- Allegro MicroSystems standard
- 16-microstep capability (smooth motion)
- Current limiting (protect motor and Pico)
- Widely available

**Key tuning parameter**:
- Current limit potentiometer: set Vref ≈ 0.56V for safe 1.7A operation
- Measure on multimeter between Vref pin and GND

**Pinout**:
- STEP, DIR, EN to Pico GPIO (see `docs/04_hardware_setup.md`)
- VMOT, GND to 12V power supply

**Where to buy**: 
- Robocraze, IndiaStack, SRI Electronics

---

### 4. AS5600 Absolute Encoder (~₹100)

**What it is**: 12-bit I²C magnetic angle sensor

**Why it**: 
- Absolute positioning (no calibration loss on power-cycle)
- I²C interface (easy Pico integration)
- 0.088° resolution (4096 counts/rev)
- Contactless (no wear)

**Installation**:
- Position magnet on pendulum shaft
- Sensor to opposite side of housing
- I²C pull-ups (4.7 kΩ) may be needed if long wires

**Calibration**:
- Record raw count when pendulum is exactly vertical
- Update `ZERO_RAW` in firmware (see `firmware/test_encoder.py`)

**Where to buy**: 
- Robocraze, AliExpress, Adafruit (international)

---

### 5. 12V Power Supply (~₹200)

**What it is**: AC-DC regulated adapter, 12V @ ≥1A

**Why it**: 
- NEMA 17 motor rated 12V
- A4988 input range 8V–35V (12V safe middle ground)
- Regulated (smooth operation, stable encoder readings)

**Critical spec**: 
- **Minimum 1A output** (motor draws 1.7A peak, but practical average ~0.8A during balancing)
- Decoupling capacitor (100µF, 25V) on VMOT for back-EMF spike protection

**Where to buy**: 
- Local electronics shop (cheapest, no shipping)
- Amazon India, Flipkart

**Alternative**:
- Lab-grade bench supply (if available)

---

### 6. USB Data Cable (~₹300)

**What it is**: USB-C to USB-A for Pico programming

**Why it**: 
- Pico has USB-C
- Powers Pico during development
- Necessary for `mpremote` serial communication

**Note**: Must be **data cable** (not charge-only). Test if unsure.

**Where to buy**: 
- Local mobile store, Amazon

---

### 7. Jumper Wires & Breadboard (~₹500)

**What it is**: Prototyping wiring and mini-breadboard

**Why it**: 
- For A4988 ↔ Pico connections (no soldering required)
- Testing and debugging
- Reversible (easy to reconfigure)

**Recommended**: 
- 1× mini breadboard (₹150)
- 1× pack M-M jumper wires 20cm (₹80)
- 1× pack M-F jumper wires (₹100)

**Alternative**: Solder directly if you're confident (saves ₹400, but less reversible).

---

### 8. 3D Printed Structural Components (~₹900)

**What it is**: Mechanical housing for pendulum and arm

**Why it**: 
- Motor mount bracket
- Arm support beam (7 cm length)
- Pendulum shaft and bob
- Cable management clips

**Material**: PLA (standard, low cost)

**Print parameters**:
- Layer height: 0.2 mm
- Infill: 20% (sufficient for low-speed balancing)
- Print time: ~12-14 hours total

**Where to get**:
- Local college makerspace (often ₹800-1200)
- DIY Labs, Make2Learn (Bangalore, etc.)
- Online services (local print-on-demand, ~₹1000-1500 due to shipping)

**Cost optimization**:
- If you have access to a college lab, cost drops to ₹300-500 material only
- Reuse existing mechanical mounts if available

**Files**: See `hardware/stl/README.md`

---

### 9. Miscellaneous (~₹500 buffer)

- M3 screws, nuts (₹50)
- Double-sided tape (₹30)
- Prototyping tape/hot glue (₹30)
- Wastage buffer (broken prints, bad solder joints, etc.) (₹300)

---

## Assembly Checklist

### Step 1: Mechanical Assembly (2-3 hours)

- [ ] 3D print all parts successfully
- [ ] Assemble motor to arm bracket
- [ ] Attach pendulum shaft to arm tip
- [ ] Install AS5600 sensor housing
- [ ] Mount AS5600 magnet on pendulum shaft
- [ ] Ensure arm rotates freely ±60° without binding
- [ ] Verify pendulum is balanced (bob centered) when hanging

### Step 2: Electronics Assembly (1-2 hours)

- [ ] Insert Pico into breadboard
- [ ] Insert A4988 into breadboard
- [ ] Connect A4988 STEP → Pico GP2
- [ ] Connect A4988 DIR → Pico GP3
- [ ] Connect A4988 EN → Pico GP4
- [ ] Connect A4988 GND to power supply GND and Pico GND (common ground)
- [ ] Connect A4988 VMOT → 12V power supply
- [ ] Connect A4988 motor coil 1 → motor phase A
- [ ] Connect A4988 motor coil 2 → motor phase B
- [ ] Connect AS5600 SDA → Pico GP8
- [ ] Connect AS5600 SCL → Pico GP9
- [ ] Connect AS5600 GND to common GND
- [ ] Connect AS5600 VCC to 3.3V (from Pico)
- [ ] **Critical**: Add 100µF capacitor across VMOT and GND (back-EMF protection)

### Step 3: Power-Up Test (15 min)

- [ ] **DO NOT enable motor yet**
- [ ] Plug 12V adapter (motor disabled)
- [ ] Measure voltage on A4988 VMOT: should be ~12V
- [ ] Connect USB to Pico
- [ ] Run `test_i2c_scan.py` → AS5600 should respond at 0x36
- [ ] Measure Vref on A4988: set to 0.56V with potentiometer
- [ ] Run `test_encoder.py` → motor still disabled, just reads angles
- [ ] Run `test_stepper.py` → small test pulses, motor rotates gently
- [ ] If all pass: ready for `main-lin.py`

---

## Tuning for Your Hardware

After assembly, follow [`firmware/README.md`](../firmware/README.md) section "Typical Bring-up Sequence":

1. Run all 6 tests in order
2. Record `ZERO_RAW` from `test_encoder.py`
3. Flash `main-lin.py` with `ZERO_RAW` set
4. Hold pendulum upright (within ±30°)
5. Observe serial output → should balance

**Working gains for our hardware** (as of this build):
- `KP = 150.0`
- `KD = 42.0`

If your system is unstable or sluggish, see [`docs/05_tuning_guide.md`](../docs/05_tuning_guide.md) for adjustment procedure.

---

## Troubleshooting During Assembly

| Problem | Symptom | Fix |
|---------|---------|-----|
| Motor won't turn | No motion on test | Check motor coil wires, verify Vref set correctly |
| Sensor not detected | I²C scan fails | Check SDA/SCL wiring, verify 3.3V on sensor |
| Erratic motion | Jittering, random steps | Check cable routing (away from motor), add ferrite clamp |
| High current draw | Power supply shuts off | Reduce current limit on A4988 (Vref down), check for mechanical binding |
| Pendulum swings wildly | Unstable in first tests | Reduce KP by 50%, increase KD, verify ZERO_RAW is correct |

---

## Procurement Timeline

| Component | Lead Time | Availability |
|-----------|-----------|--------------|
| Pico, A4988, Stepper, AS5600 | 2-3 days | Local (Robocraze, IndiaStack) |
| Power supply | Same day | Local electronics shop |
| USB cable | Same day | Local mobile store |
| Jumper wires, breadboard | 1-2 days | Local or online |
| 3D printing | 1-2 days | College makerspace |
| **Total** | **3-5 days** | If sourcing locally |

---

## Quality Checklist Before Powering Up

- [ ] All solder joints shiny (if soldered)
- [ ] No loose wires touching unexpectedly
- [ ] Motor coil impedance ~10Ω per phase (quick check with multimeter)
- [ ] Decoupling capacitor installed
- [ ] Common ground between all subsystems
- [ ] Pico USB cable is data cable (test with known device first)
- [ ] Mechanical: arm rotates smoothly, no grinding

---

## Cost Reduction Tips

**If building multiple units**:
- Buy motors in bulk: ₹500 per unit (vs ₹600 single)
- 3D printing material cost drops by 30% (printer amortization)
- USB cables (reuse from existing devices)

**If you have lab access**:
- Power supply: use bench supply instead of adapter (₹0)
- 3D printing: use college printer (₹200-300 material only)
- Jumper wires: scrap from old projects
- **Adjusted cost: ₹2000-2500**

**If you source internationally** (AliExpress, longer lead):
- Motor, driver, sensor cost ~40-50% less
- But shipping + delays (2-3 weeks)
- Worthwhile if building many units

---

## Next Steps

1. Gather parts using the BOM above
2. Print 3D parts (allow 12-14 hours)
3. Follow Assembly Checklist
4. Run test suite (`make test`)
5. Flash controller (`make main linear`)
6. Enjoy balanced pendulum! 🎉

For detailed firmware instructions, see [`firmware/README.md`](../firmware/README.md).

For theory, see [`docs/01_physics.md`](../docs/01_physics.md) and [`docs/02_control_design.md`](../docs/02_control_design.md).

---
