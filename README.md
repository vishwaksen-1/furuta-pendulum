# Furuta Pendulum — Rotary Inverted Pendulum

**Design Lab Project — EECE Department, IIT Kharagpur**

---

> *We gratefully acknowledge the guidance and support of our professor Ritwik Kumar Layek throughout this project.*
> *Special thanks to our friend Akshit Kumar from the Mechanical Engineering Department for his time and effort in designing and 3D printing the mechanical components.*

---

## Team

| Name | Github |
|------|--------|
| Vishwaksen Reddy D| [@vishwaksen-1](https://github.com/vishwaksen-1) |
| Venkata Nikhil Reddy Chinta| [@nikki041905](https://github.com/nikki041905) |
| Charan Reddy Bokkka | [@charan1304](https://github.com/charan1304) |
| Anumala Rushendra Reddy| [@rushendra-1](https://github.com/rushendra-1) |

**Course:** Design Lab — EECE Department, IIT Kharagpur
**Semester:** Spring 2026
**Faculty Advisor:** Prof. Ritwik Kumar Layek
---

## What This Is

A **Furuta pendulum** (rotary inverted pendulum) is a classic unstable control systems benchmark. A horizontal arm rotates freely on a motor axis; a pendulum hangs from the tip of the arm and must be kept upright by rotating the arm — the system has no direct uprighting actuator, only the inertial coupling between arm and pendulum.

This repository documents our full build: the physics derivation, control design, hardware selection, circuit wiring, MicroPython firmware, and test procedures — on a budget suitable for a college lab project.

**Scope:** Balance-only. The pendulum is started upright and the controller rejects disturbances. No swing-up is implemented.

---

## Hardware

| Component | Part | Role |
|-----------|------|------|
| Microcontroller | Raspberry Pi Pico | Control loop, step generation, I²C |
| Base motor | 17HS4401S NEMA 17 Stepper | Rotates horizontal arm |
| Motor driver | A4988 | Microstepping driver for stepper |
| Pendulum encoder | AS5600 | 12-bit magnetic angle sensor |
| Power supply | 12V ≥ 2A | Motor voltage rail |
| Decoupling cap | 100 µF 25V electrolytic | Back-EMF protection on VMOT |

**Key mechanical specs:**
- Arm length: 7 cm
- Pendulum length: 11 cm
- Pendulum mass: ~30 g
- Total rotating mass: < 90 g
- Arm rotation limit: ±60° (cable wrap constraint from AS5600 wiring)

---

## Repository Structure

```
furuta-pendulum/
│
├── README.md                        ← you are here
│
├── docs/
│   ├── 01_physics.md                ← full equations of motion, linearisation
│   ├── 02_control_design.md         ← PD pole-placement, gain derivation
│   ├── 03_constraints.md            ← hard/soft system constraints
│   ├── 04_hardware_setup.md         ← wiring, current calibration, assembly
│   └── 05_tuning_guide.md           ← step-by-step gain tuning procedure
│
├── hardware/
│   ├── wiring_diagram.md            ← full ASCII schematic + pin table
│   └── stl/                         ← 3D printed parts (add your files here)
│       └── README.md
│
├── firmware/
│   ├── README.md                    ← MicroPython setup guide + Pico flashing
│   ├── main.py                      ← main balancing controller
│   ├── test_i2c_scan.py             ← Test 1: verify AS5600 detected
│   ├── test_encoder.py              ← Test 2: angle read + zero calibration
│   ├── test_stepper.py              ← Test 3: basic motor rotation
│   ├── test_velocity.py             ← Test 4: velocity estimation quality
│   ├── test_motor_encoder.py        ← Test 5: motor characterisation via encoder
│   └── test_step_rate.py            ← Test 6: step rate controller dry run
│
└── tools/
    └── feasibility_tracker.html     ← interactive browser-based feasibility calculator
```

---

## Quick Start

1. **Read the physics** — [`docs/01_physics.md`](docs/01_physics.md)
2. **Understand the control design** — [`docs/02_control_design.md`](docs/02_control_design.md)
3. **Wire the hardware** — [`hardware/wiring_diagram.md`](hardware/wiring_diagram.md)
4. **Calibrate motor current** — [`docs/04_hardware_setup.md`](docs/04_hardware_setup.md)
5. **Flash MicroPython and run tests** — [`firmware/README.md`](firmware/README.md)
6. **Run tests in order** — H1 through H5 in `firmware/`
7. **Launch main controller** — `firmware/main.py`
8. **Tune gains** — [`docs/05_tuning_guide.md`](docs/05_tuning_guide.md)

---

## Usage

This section explains how to upload and run firmware on the Pico. Choose your preferred workflow: **Thonny** (GUI-based, beginner-friendly) or **mpremote** (CLI-based, scriptable).

### Option 1: Using Thonny IDE

**Thonny** is a beginner-friendly Python IDE with built-in MicroPython support. It handles Pico detection and file transfer automatically.

#### Windows

1. **Download & install Thonny**
   - Go to [thonny.org](https://thonny.org/) and download the Windows installer.
   - Run the installer and complete setup.

2. **Connect Pico**
   - Plug the Pico into a USB port (you will see a new COM port in Device Manager, typically `COM3` or higher).

3. **Configure Thonny**
   - Open Thonny.
   - Go to **Tools → Options → Interpreter**.
   - Select **MicroPython (Raspberry Pi Pico)** from the dropdown.
   - Thonny will auto-detect the COM port; confirm it shows your Pico.
   - Click **OK**.

4. **Upload and run firmware**
   - In Thonny, open the file you want to upload (e.g., `firmware/test_i2c_scan.py`).
   - Click **File → Save as…** → choose **Pico** as the target.
   - Enter the filename (e.g., `test_i2c_scan.py`) and click **Save**.
   - The file is now on the Pico. To run it, click the **Run** button (▶) or press `F5`.

5. **View output**
   - The Shell tab at the bottom shows your program output in real time.

#### Linux

1. **Install Thonny via package manager**
   ```bash
   sudo apt update
   sudo apt install thonny
   ```
   Or download from [thonny.org](https://thonny.org/).

2. **Add your user to the dialout group** (to access `/dev/ttyACM0` without root)
   ```bash
   sudo usermod -a -G dialout $USER
   ```
   Log out and back in for the change to take effect.

3. **Connect Pico**
   - Plug the Pico into a USB port. It appears as `/dev/ttyACM0` (or similar).

4. **Configure Thonny**
   - Open Thonny.
   - Go to **Tools → Options → Interpreter**.
   - Select **MicroPython (Raspberry Pi Pico)** from the dropdown.
   - Thonny will auto-detect the device; confirm it shows `/dev/ttyACM0`.
   - Click **OK**.

5. **Upload and run firmware**
   - Same as Windows (steps 4–5 above).

---

### Option 2: Using mpremote CLI

**mpremote** is Raspberry Pi's command-line tool for MicroPython. It is ideal for scripting, CI/CD, and headless workflows.

#### Windows

1. **Install mpremote**
   - Ensure Python 3.7+ is installed.
   - Open Command Prompt (or PowerShell) and run:
     ```cmd
     pip install mpremote
     ```

2. **Connect Pico**
   - Plug the Pico into a USB port. Note the COM port (Device Manager shows it as `COM3`, etc.).

3. **List connected devices** (check connection)
   ```cmd
   mpremote list
   ```
   You should see something like:
   ```
   COM3 – Raspberry Pi Pico (COM3)
   ```

4. **Upload a file**
   ```cmd
   mpremote cp firmware\test_i2c_scan.py :test_i2c_scan.py
   ```
   This copies `test_i2c_scan.py` from your PC to the Pico's filesystem.

5. **Run the file**
   ```cmd
   mpremote run firmware\test_i2c_scan.py
   ```
   Or, to run a file already on the Pico:
   ```cmd
   mpremote exec "import test_i2c_scan"
   ```

6. **Interactive REPL** (for real-time debugging)
   ```cmd
   mpremote
   ```
   This opens an interactive Python prompt on the Pico. Type Python commands directly. Press `Ctrl+D` to exit.

#### Linux

1. **Install mpremote from a virtual environment** (recommended)
   ```bash
   python3 -m venv /path/to/venv
   source /path/to/venv/bin/activate
   pip install mpremote
   ```
   Or, install globally:
   ```bash
   pip install mpremote
   ```

2. **Add your user to the dialout group** (to access `/dev/ttyACM0` without sudo)
   ```bash
   sudo usermod -a -G dialout $USER
   ```
   Log out and back in for the change to take effect.

3. **Connect Pico**
   - Plug the Pico into a USB port. It appears as `/dev/ttyACM0`.

4. **List connected devices** (check connection)
   ```bash
   mpremote list
   ```
   You should see:
   ```
   /dev/ttyACM0 – Raspberry Pi Pico
   ```

5. **Upload a file**
   ```bash
   mpremote cp firmware/test_i2c_scan.py :test_i2c_scan.py
   ```

6. **Run the file**
   ```bash
   mpremote run firmware/test_i2c_scan.py
   ```
   Or, to run a file already on the Pico:
   ```bash
   mpremote exec "import test_i2c_scan"
   ```

7. **Interactive REPL**
   ```bash
   mpremote
   ```
   Type Python commands directly. Press `Ctrl+D` to exit.

---

### Batch Operation Example (mpremote)

To upload and run the entire test suite in sequence:

```bash
# Linux / macOS
mpremote cp firmware/test_i2c_scan.py :test_i2c_scan.py
mpremote run firmware/test_i2c_scan.py
# ... repeat for each test
```

```cmd
REM Windows
mpremote cp firmware\test_i2c_scan.py :test_i2c_scan.py
mpremote run firmware\test_i2c_scan.py
REM ... repeat for each test
```

---

### Which Tool Should I Use?

| Task | Thonny | mpremote |
|------|--------|----------|
| **First time users** | ✅ Start here | ⚠ CLI steeper learning curve |
| **Visual file browser** | ✅ Integrated | ❌ Command line only |
| **Debugging live code** | ✅ Built-in REPL | ✅ Interactive mode |
| **Automated scripts** | ❌ Not easily scriptable | ✅ Perfect for CI/CD |
| **macOS/Linux/Windows** | ✅ All platforms | ✅ All platforms |

**Recommendation:** Start with **Thonny** if you are new to MicroPython. Switch to **mpremote** once you need scripting or prefer the command line.

---

## Feasibility Tracker

An interactive browser tool to verify that your specific hardware parameters (pendulum length, arm length, mass, microstepping, step rate) satisfy the physics and control bandwidth requirements before you build anything.

**→ Open [`tools/feasibility_tracker.html`](tools/feasibility_tracker.html) in any browser. No server needed.**

The tracker computes: natural frequency ωₙ, fall time, motor torque budget, acceleration authority ratio, encoder resolution, I²C timing budget, and constraint checklist — all from first principles derived in the physics doc.

---

## Results Summary

> *Fill this in after your first successful balance run.*

| Metric | Value |
|--------|-------|
| Final Kp | — |
| Final Kd | — |
| Steady-state error | — |
| Max disturbance rejected | — |
| Loop rate achieved | — Hz |

---

## License

MIT License. See `LICENSE` file.
Hardware designs (STL files) are released under CC BY 4.0.

---

## References

1. K. J. Åström & K. Furuta, "Swinging up a pendulum by energy control," *Automatica*, 2000.
2. Ogata, K. *Modern Control Engineering*, 5th ed. Prentice Hall.
3. AS5600 Datasheet — ams OSRAM.
4. A4988 Stepper Motor Driver Datasheet — Allegro MicroSystems.
5. Raspberry Pi Pico MicroPython documentation — [micropython.org](https://micropython.org/download/rp2-pico/)
