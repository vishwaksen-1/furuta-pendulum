# Thonny Workflow Guide (Alternative to mpremote)

This guide is for users who prefer a graphical IDE workflow. The primary and recommended workflow for this repository is mpremote + Makefile (see [firmware/README.md](../firmware/README.md)).

## 1. Install Thonny

Download and install Thonny from:

- https://thonny.org

## 2. Flash MicroPython on Pico

1. Download Raspberry Pi Pico MicroPython UF2:
   - https://micropython.org/download/rp2-pico/
2. Hold BOOTSEL while plugging in Pico.
3. Drag the UF2 onto the RPI-RP2 drive.
4. Pico reboots into MicroPython.

## 3. Configure Thonny Interpreter

1. Open Thonny.
2. Go to Tools -> Options -> Interpreter.
3. Set interpreter to MicroPython (Raspberry Pi Pico).
4. Select the detected serial port.

## 4. Upload and Run Test Scripts

Upload one script at a time as main.py on the Pico and run.

Suggested order:

1. firmware/test_i2c_scan.py
2. firmware/test_encoder.py
3. firmware/test_stepper.py
4. firmware/test_velocity.py
5. firmware/test_motor_encoder.py
6. firmware/test_step_rate.py

## 5. Upload and Run Main Controller

Use one of:

- firmware/main-lin.py
- firmware/main-nl-p.py
- firmware/main-nl-full.py

Save the selected file to Pico as main.py and run/restart.

## 6. Notes

- Set ZERO_RAW using output from test_encoder.py.
- Keep pendulum upright before activating control.
- If you later switch to CLI automation, use the mpremote guide in [firmware/README.md](../firmware/README.md).
