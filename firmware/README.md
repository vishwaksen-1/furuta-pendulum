# Firmware

MicroPython code for the Raspberry Pi Pico. Run the test suite in order before running the main controller.

---

## Project Structure

```
firmware/
├── main.py                  ← Unified main controller (selectable strategy)
├── control_lib.py           ← Shared hardware & control utilities
├── control_strategies.py    ← PD and LQR controller implementations
├── test/                    ← Test suite (run in order)
│   ├── test_i2c_scan.py     (Test 1)
│   ├── test_encoder.py      (Test 2)
│   ├── test_stepper.py      (Test 3)
│   ├── test_velocity.py     (Test 4)
│   ├── test_motor_encoder.py (Test 5)
│   ├── test_step_rate.py    (Test 6)
│   └── speed_test.py        (Motor characterization)
├── main-lin.py              ← Legacy: PD controller (reference)
├── main-lqr.py              ← Legacy: LQR controller (reference)
└── README.md                ← This file
```

---

## MicroPython Setup — Flash the Pico

### Step 1: Download MicroPython firmware

Go to the official MicroPython download page for the Pico:

**→ https://micropython.org/download/rp2-pico/**

Download the latest stable `.uf2` file.

### Step 2: Flash

1. Hold the **BOOTSEL** button on the Pico.
2. While holding BOOTSEL, connect the Pico to your computer via USB.
3. Release BOOTSEL. The Pico appears as a USB mass storage device called `RPI-RP2`.
4. Drag and drop the `.uf2` file onto the `RPI-RP2` drive.
5. The Pico reboots automatically and is now running MicroPython.

### Step 3: Install Thonny IDE (recommended for beginners)

Download from **https://thonny.org**

In Thonny:
- Go to **Tools → Options → Interpreter**
- Select **MicroPython (Raspberry Pi Pico)**
- Select the correct COM port

You can now open any `.py` file from this folder, click Run, and it executes on the Pico.

### Step 4: Copy files to Pico

Using Thonny's file browser (View → Files), copy all `.py` files from `firmware/` onto the Pico root. The Pico's filesystem appears in the bottom panel.

> Alternatively, use `mpremote` from the command line:
> ```bash
> mpremote cp firmware/main.py :main.py
> mpremote cp firmware/control_lib.py :control_lib.py
> mpremote cp firmware/control_strategies.py :control_strategies.py
> ```

---

## Running Tests

### Using Make (Recommended)

```bash
# Run all tests in order
make test

# Run specific test (1–6)
make test 1
make test 2

# Or run speed_test.py directly
mpremote cp firmware/test/speed_test.py :main.py
mpremote reset
```

### Using Thonny

1. Open `firmware/test/test_i2c_scan.py`
2. Click **Run**
3. Complete all 6 tests in order

---

## Running the Main Controller

### Using Make (Recommended)

```bash
# Flash with PD control strategy
make main pd

# Flash with LQR control strategy
make main lqr

# Or flash and start interactive REPL session
make run-pd      # PD strategy
make run-lqr     # LQR strategy
```

### Manually

```bash
mpremote cp firmware/main.py :main.py
mpremote cp firmware/control_lib.py :control_lib.py
mpremote cp firmware/control_strategies.py :control_strategies.py
mpremote reset
```

### To change control strategy:

Edit `firmware/main.py`, line ~17:

```python
# Choose one strategy:
#   "pd"       → Traditional PD (2D feedback: φ, φ̇)
#   "lqr"      → Optimal LQR (4D feedback: φ, φ̇, θ, θ̇)
#   "nl-p"     → Nonlinear P only (log on proportional term)
#   "nl-full"  → Nonlinear full PD (log on entire PD feedback)
CONTROL_STRATEGY = "pd"
```

Then re-flash and reset.

---

## Test Suite Reference

| File | Purpose | Order |
|------|---------|-------|
| `test/test_i2c_scan.py` | Verify AS5600 on I²C bus | 1st |
| `test/test_encoder.py` | Find ZERO_RAW offset, check noise | 2nd |
| `test/test_stepper.py` | Motor rotation both directions | 3rd |
| `test/test_velocity.py` | Velocity estimate quality | 4th |
| `test/test_motor_encoder.py` | Motor characterization via deflection | 5th |
| `test/test_step_rate.py` | Step rate controller timing | 6th |
| `test/speed_test.py` | Comprehensive motor speed/accel limits | Optional |

---

## Before Running main.py

1. ✅ Complete all six tests successfully
2. 📝 Open `main.py` and set `ZERO_RAW` to the value from `test_encoder.py`
3. ⚙️ Choose control strategy: `CONTROL_STRATEGY = "pd"` or `"lqr"`
4. 🎯 Start with **conservative gains** (already set as default)
5. 📚 Follow tuning procedure: [`../docs/05_tuning_guide.md`](../docs/05_tuning_guide.md)

---

## Serial Monitor Output

All scripts print status over USB serial at 115200 baud. In Thonny, output appears in the Shell panel. From a terminal:

```bash
# Linux / macOS
screen /dev/ttyACM0 115200

# Or use mpremote shell
mpremote

# Windows — use PuTTY or Thonny Shell
```

Press **Ctrl+C** to stop. The motor will be disabled on KeyboardInterrupt.

---

## File Reference: Main Controller

### `main.py`
Unified balancing controller supporting multiple strategies:
- Imports `control_lib.py` for hardware abstraction
- Imports `control_strategies.py` to instantiate PDController or LQRController
- State machine: IDLE → ACTIVE → RECOVERING / LIMIT_HIT → FAULT
- **Edit to select strategy** (line ~15) and tune parameters

### `control_lib.py`
Shared hardware utilities:
- Motor control (enable, disable, fire steps, step rate ramp)
- Sensor reading (AS5600 angle, velocity estimation)
- Arm centering (virtual spring)
- Calibration routines
- State machine constants

### `control_strategies.py`
Control implementations:
- **`PDController`**: Traditional PD feedback (2D state: φ, φ̇)
- **`LQRController`**: Optimal state-feedback (4D state: φ, φ̇, θ, θ̇)
- **`NLPController`**: Nonlinear P-only (logarithmic scaling on proportional term only)
- **`NLFullController`**: Nonlinear full PD (logarithmic scaling on entire PD term)
- **`get_controller()`**: Factory function to instantiate by name

### `main-lin.py` & `main-lqr.py`
Legacy monolithic implementations (kept for reference/comparison).

---

## Pico Pinout Reference (Used Pins)

```
                    ┌──────────┐
               GP0  │  1   40  │ VBUS
               GP1  │  2   39  │ VSYS  ← USB power in
               GND  │  3   38  │ GND
               GP2  │  4   37  │ 3V3EN
               GP3  │  5   36  │ 3V3   ← logic power out
               GP4  │  6   35  │ ADC_VREF
               GP5  │  7   34  │ GP28
               GND  │  8   33  │ GND
               GP6  │  9   32  │ GP27
               GP7  │ 10   31  │ GP26
  AS5600 SDA ─ GP8  │ 11   30  │ RUN
  AS5600 SCL ─ GP9  │ 12   29  │ GP22
               GND  │ 13   28  │ GND
              GP10  │ 14   27  │ GP21
              GP11  │ 15   26  │ GP20
              GP12  │ 16   25  │ GP19
              GP13  │ 17   24  │ GP18
               GND  │ 18   23  │ GND
              GP14  │ 19   22  │ GP17
              GP15  │ 20   21  │ GP16
                    └──────────┘

  GP2 → STEP     GP3 → DIR     GP4 → ENABLE
  GP8 → SDA      GP9 → SCL
```

---

## Troubleshooting

- **Motor doesn't move**: Check EN pin (should be low when enabled). Check Vref on A4988 (aim for 0.56V).
- **Velocity noise too high**: Lower `ALPHA_EMA` in `main.py` (trade accuracy for noise).
- **Pendulum unstable**: Verify ZERO_RAW is correct. Check control gains. Start conservative.
- **I²C errors**: Check SDA/SCL wiring to AS5600. Add 4.7 kΩ pull-up resistors if missing.

---

## Makefile Targets

See `../Makefile`:

```bash
make test          # Run all tests in order
make test 1        # Run test 1 only
make main pd       # Flash and run main with PD strategy
make main lqr      # Flash and run main with LQR strategy
make run-pd        # Flash PD and open interactive REPL
make run-lqr       # Flash LQR and open interactive REPL
make clean         # Remove compiled cache
```
