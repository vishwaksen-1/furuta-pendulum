# test_step_rate.py
# Test 6 of 6 — Step rate controller dry run.
# Tests the trapezoidal velocity profile and timing in isolation.
# No pendulum control — validates the stepper command pipeline only.
# Final arm position should be near 0° if ramps are symmetric.

from machine import Pin
import time, math

STEP_PIN      = Pin(2, Pin.OUT)
DIR_PIN       = Pin(3, Pin.OUT)
EN_PIN        = Pin(4, Pin.OUT)

STEPS_PER_REV = 1600
MAX_STEP_RATE  = 8000.0      # steps/s ceiling
MAX_STEP_ACCEL = 5120000.0/8     # steps/s² ramp rate

step_rate  = 0.0
step_accum = 0.0
step_count = 0

def enable():  EN_PIN.value(0)
def disable(): EN_PIN.value(1)

def update_stepper(target_rate, dt):
    global step_rate, step_accum, step_count
    max_delta = MAX_STEP_ACCEL * dt
    error = target_rate - step_rate
    if abs(error) <= max_delta:
        step_rate = target_rate
    else:
        step_rate += math.copysign(max_delta, error)
    step_rate = max(-MAX_STEP_RATE, min(MAX_STEP_RATE, step_rate))

    step_accum += step_rate * dt
    steps = int(step_accum)
    step_accum -= steps

    if steps:
        DIR_PIN.value(1 if steps > 0 else 0)
        time.sleep_us(2)
        for _ in range(abs(steps)):
            STEP_PIN.value(1); time.sleep_us(2)
            STEP_PIN.value(0); time.sleep_us(2)
        step_count += steps
    return steps

DT_MS = 2
DT_S  = DT_MS / 1000.0

# Profile: ramp up, hold, ramp down, reverse, return
profile = [
    (400, 300),    # ramp to +400 steps/s, hold 300 ms
    (0,   300),    # ramp to 0
    (-400, 300),   # ramp to -400 steps/s
    (0,   300),    # ramp back to 0
]

enable()
print("=== Step Rate Controller Test ===")
print(f"  MAX_STEP_RATE = {MAX_STEP_RATE} steps/s")
print(f"  MAX_STEP_ACCEL = {MAX_STEP_ACCEL} steps/s²")
print(f"  Loop dt = {DT_MS} ms  ({1000//DT_MS} Hz)\n")
print(f"  {'target':>7}  {'actual':>8}  {'θ_arm_deg':>10}  {'step_count':>10}")

for (target_rate, dur_ms) in profile:
    n_loops = dur_ms // DT_MS
    for i in range(n_loops):
        t0 = time.ticks_us()
        update_stepper(target_rate, DT_S)
        theta_deg = step_count / STEPS_PER_REV * 360.0

        if i % 25 == 0:
            print(f"  {target_rate:7.0f}  {step_rate:8.1f}  {theta_deg:10.2f}°  {step_count:10d}")

        elapsed = time.ticks_diff(time.ticks_us(), t0)
        time.sleep_us(max(0, DT_MS * 1000 - elapsed))

disable()
theta_final = step_count / STEPS_PER_REV * 360.0
print(f"\nFinal: step_count = {step_count},  θ = {theta_final:.2f}°")
print(f"Should be close to 0°. Error indicates accumulation in ramp timing.")
