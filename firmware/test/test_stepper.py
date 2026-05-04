# test_stepper.py
# Test 3 of 6 — Basic motor rotation in both directions.
# Confirms wiring, direction, and step smoothness.
# Motor should be warm (not hot) after the test — confirms current is set.

from machine import Pin
import time

STEP_PIN = Pin(2, Pin.OUT)
DIR_PIN  = Pin(3, Pin.OUT)
EN_PIN   = Pin(4, Pin.OUT)

# MS pins set here in case wired to GPIO.
# If hard-wired to VCC/GND on the board, these lines have no effect but are harmless.
MS1 = Pin(5, Pin.OUT); MS1.value(1)   # HIGH
MS2 = Pin(6, Pin.OUT); MS2.value(1)   # HIGH
MS3 = Pin(7, Pin.OUT); MS3.value(0)   # LOW  → 1/8 step

STEPS_PER_REV = 1600   # 200 base × 8 microsteps

def enable():  EN_PIN.value(0)   # active LOW
def disable(): EN_PIN.value(1)

def step_motor(n_steps, direction, step_delay_us=2000):
    """
    Step motor n_steps in given direction.
    step_delay_us: half-period of STEP pulse.
    2000 µs → 250 steps/s → ~9.4 RPM at 1/8 step (slow and safe).
    """
    DIR_PIN.value(direction)
    time.sleep_us(5)   # DIR setup time required by A4988 (min 200 ns)
    for _ in range(n_steps):
        STEP_PIN.value(1)
        time.sleep_us(step_delay_us)
        STEP_PIN.value(0)
        time.sleep_us(step_delay_us)

print("=== Stepper Motor Test ===\n")
print("Enabling motor...")
enable()
time.sleep_ms(100)

print("1. Rotating CW — 1 full revolution at slow speed...")
step_motor(STEPS_PER_REV, direction=1, step_delay_us=2000)
time.sleep_ms(500)

print("2. Rotating CCW — 1 full revolution at slow speed...")
step_motor(STEPS_PER_REV, direction=0, step_delay_us=2000)
time.sleep_ms(500)

print("3. Fast spin test (800 steps/s — safe ceiling)...")
step_motor(STEPS_PER_REV // 2, direction=1, step_delay_us=625)
time.sleep_ms(500)
step_motor(STEPS_PER_REV // 2, direction=0, step_delay_us=625)
time.sleep_ms(500)

print("\nDone. Motor should be warm to the touch — not hot.")
print("If motor twitches but does not rotate: coil pair may be wrong. Swap A+ and A−.")
print("If motor spins wrong direction: swap DIR logic or swap one coil pair.")

disable()
print("Motor disabled.")
