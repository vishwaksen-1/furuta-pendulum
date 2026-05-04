# Firmware

MicroPython code for the Raspberry Pi Pico. Run the test scripts in order before running the main controller.

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

Using Thonny's file browser (View → Files), copy all `.py` files from this folder onto the Pico. The Pico's filesystem appears in the bottom panel.

> Alternatively, use `mpremote` from the command line:
> ```
> pip install mpremote
> mpremote cp firmware/*.py :
> ```

---

## File Reference

| File | Purpose | Run order |
|------|---------|-----------|
| `test_i2c_scan.py` | Verify AS5600 is detected on I²C bus | 1st |
| `test_encoder.py` | Read angle, find zero offset, check noise | 2nd |
| `test_stepper.py` | Basic motor rotation in both directions | 3rd |
| `test_velocity.py` | Evaluate velocity estimate quality | 4th |
| `test_motor_encoder.py` | Characterise motor using encoder deflection | 5th |
| `test_step_rate.py` | Validate step rate controller timing | 6th |
| `main.py` | Full balancing controller | Last |

---

## Before Running main.py

1. Complete all six tests successfully.
2. Open `main.py` and set `ZERO_RAW` to the value from `test_encoder.py`.
3. Start with the **conservative gains** (already set as default).
4. Follow the tuning procedure in [`../docs/05_tuning_guide.md`](../docs/05_tuning_guide.md).

---

## Serial Monitor

All scripts print status over USB serial at 115200 baud. In Thonny, output appears in the Shell panel. From a terminal:

```bash
# Linux / macOS
screen /dev/ttyACM0 115200

# Windows — use PuTTY or Thonny Shell
```

Press **Ctrl+C** to stop any running script. The motor will be disabled on KeyboardInterrupt.

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
