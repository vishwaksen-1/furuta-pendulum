# Firmware (mpremote Workflow)

This firmware guide is for command-line users only. It assumes you use `mpremote` directly or through the repository `Makefile`.

If you prefer a GUI workflow, use the Thonny guide at the end of this document.

---

## 1. Python Requirements

Install host-side tooling from the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Current dependency list is in `requirements.txt`:

- `mpremote`

Verify installation:

```bash
mpremote --version
```

---

## 2. Flash MicroPython to Pico

1. Download UF2 from https://micropython.org/download/rp2-pico/
2. Hold BOOTSEL and plug in Pico.
3. Drag UF2 to `RPI-RP2` drive.
4. Pico reboots into MicroPython.

Check device visibility:

```bash
mpremote list
```

On Linux, if permission is denied on `/dev/ttyACM0`:

```bash
sudo usermod -a -G dialout $USER
```

Then log out and back in.

---

## 3. Firmware Files and Controller Modes

Main control entry files:

- `main-lin.py` - baseline linear PD
- `main-nl-p.py` - nonlinear P variant
- `main-nl-full.py` - nonlinear full variant
- `main-lqr.py` - **⚠️ EXPERIMENTAL**: LQR state-feedback control (NOT YET TESTED on hardware; LQR gain matrix must be tuned experimentally; see [`../docs/06_lqr_control.md`](../docs/06_lqr_control.md))

Test scripts (run in order):

1. `test_i2c_scan.py`
2. `test_encoder.py`
3. `test_stepper.py`
4. `test_velocity.py`
5. `test_motor_encoder.py`
6. `test_step_rate.py`

---

## 4. Direct mpremote Usage (without Makefile)

### Flash and Run a Test

```bash
mpremote fs cp firmware/test_i2c_scan.py :main.py
mpremote reset
```

### Flash and Run a Controller

```bash
mpremote fs cp firmware/main-lin.py :main.py
mpremote reset
```

### Manually Run a File with Live Output

To run a main file and see serial output in real-time without interactive mode:

```bash
# Flash and execute in one go, stream output
mpremote fs cp firmware/main-lin.py :main.py
mpremote run :main.py
```

Or execute a file already on the Pico:

```bash
mpremote exec "exec(open('main.py').read())"
```

### Interactive REPL (for debugging)

Open interactive Python prompt on the Pico:

```bash
mpremote
```

From the REPL, you can:
- Import and run functions directly
- Test sensors and motor commands
- Press `Ctrl+D` to exit

---

## 5. Makefile Workflow (recommended)

The `Makefile` is a thin wrapper around `mpremote` and is the fastest day-to-day workflow.

From repository root:

```bash
make help
```

Run tests:

```bash
# Run all tests in sequence
make test

# Run a specific test
make test 1
make test 6
```

Flash controller modes:

```bash
make main linear
make main nl 1
make main nl 2
```

Notes:

- `make main linear` flashes `firmware/main-lin.py` as `:main.py`
- `make main nl 1` flashes `firmware/main-nl-p.py` as `:main.py`
- `make main nl 2` flashes `firmware/main-nl-full.py` as `:main.py`

If your `mpremote` is in a custom virtual environment:

```bash
make VENV=$HOME/path/to/venv test
```

Or override executable directly:

```bash
make MPREMOTE=$HOME/path/to/mpremote test
```

---

## 6. Typical Bring-up Sequence

1. Flash MicroPython UF2.
2. Run `make test`.
3. From `test_encoder.py`, record and update `ZERO_RAW` in selected `main-*.py`.
4. Flash desired control mode (`make main linear` or nonlinear modes).
5. Hold pendulum upright and observe serial output.

---

## 7. Serial and Safety Notes

- Use `mpremote` interactive mode for live logs.
- Press `Ctrl+C` to interrupt.
- Ensure motor is disabled before rewiring.
- Keep wiring clear of moving arm before enabling control.

---

## 8. Troubleshooting

- Device not found: run `mpremote list`; reconnect USB cable.
- Permission denied on Linux: add user to `dialout` group.
- No motion: verify A4988 enable/dir/step pins and motor supply.
- Unstable behavior: verify `ZERO_RAW`, run tests again, then retune gains.

---

## 9. Alternative GUI Workflow (Thonny)

For users who prefer Thonny, use:

- [Thonny Guide](../docs/07_thonny_guide.md)
