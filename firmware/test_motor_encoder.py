# test_motor_encoder.py
# Test 5 of 6 — Motor characterisation via pendulum encoder deflection.
#
# Key insight: when the arm accelerates, the freely-hanging pendulum
# deflects due to inertia. This deflection directly encodes arm acceleration:
#
#   a_tangential = g × tan(φ) ≈ g × φ   (small angle)
#   θ̈_arm = a_tangential / r
#
# This lets us measure ACTUAL motor acceleration, step loss, resonance,
# and settling — without any additional sensor.
#
# SETUP: Run this with pendulum hanging freely DOWNWARD (not upright).
#        The deflection physics only work cleanly in the hanging position.

from machine import Pin, I2C
import time, math

STEP_PIN = Pin(2, Pin.OUT)
DIR_PIN  = Pin(3, Pin.OUT)
EN_PIN   = Pin(4, Pin.OUT)
i2c      = I2C(0, sda=Pin(8), scl=Pin(9), freq=400_000)

AS5600_ADDR   = 0x36
STEPS_PER_REV = 1600
ARM_LENGTH_M  = 0.07    # arm length in metres

def motor_enable():  EN_PIN.value(0)
def motor_disable(): EN_PIN.value(1)

def read_raw_angle():
    d = i2c.readfrom_mem(AS5600_ADDR, 0x0C, 2)
    return ((d[0] & 0x0F) << 8) | d[1]

# Zero encoder with pendulum hanging still
input("Let pendulum hang freely and still. Press ENTER to zero...")
ZERO_RAW = read_raw_angle()
print(f"Zero set to raw = {ZERO_RAW}\n")

def read_phi_rad():
    raw   = read_raw_angle()
    delta = raw - ZERO_RAW
    if delta >  2048: delta -= 4096
    if delta < -2048: delta += 4096
    return delta * (2 * math.pi / 4096)

# Step rate controller
step_rate  = 0.0
step_accum = 0.0
step_count = 0

def update_stepper(target_rate, dt, max_accel=4000):
    global step_rate, step_accum, step_count
    max_delta = max_accel * dt
    error     = target_rate - step_rate
    step_rate += math.copysign(min(abs(error), max_delta), error) if error else 0
    step_rate  = max(-800.0, min(800.0, step_rate))
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

DT_MS = 2
DT_S  = DT_MS / 1000.0

def run_profile(name, profile, max_accel=4000):
    """Run a step rate profile and log encoder + inferred acceleration."""
    global step_rate, step_accum, step_count
    step_rate = 0.0; step_accum = 0.0; step_count = 0
    log = []
    t_total = 0

    print(f"\n{'─'*60}")
    print(f"  {name}")
    print(f"{'─'*60}")
    print(f"  {'t_ms':>5}  {'target':>7}  {'actual_rate':>11}  {'φ_deg':>7}  {'θ̈_arm':>12}  {'steps':>7}")

    motor_enable()

    for (target_rate, dur_ms) in profile:
        for _ in range(dur_ms // DT_MS):
            t0  = time.ticks_us()
            phi = read_phi_rad()

            a_tan      = 9.81 * math.tan(phi)         # tangential accel (m/s²)
            theta_ddot = a_tan / ARM_LENGTH_M          # arm angular accel (rad/s²)

            update_stepper(target_rate, DT_S, max_accel)

            log.append({
                't_ms':       t_total,
                'target':     target_rate,
                'step_rate':  step_rate,
                'phi_deg':    math.degrees(phi),
                'accel_meas': theta_ddot,
                'steps':      step_count,
            })

            if t_total % 100 == 0:
                print(f"  {t_total:5d}  {target_rate:7.0f}  {step_rate:11.1f}  "
                      f"{math.degrees(phi):7.2f}°  {theta_ddot:+10.1f} r/s²  {step_count:7d}")

            t_total += DT_MS
            elapsed  = time.ticks_diff(time.ticks_us(), t0)
            time.sleep_us(max(0, DT_MS * 1000 - elapsed))

    motor_disable()
    return log

def analyse(log, name):
    phi_max   = max(abs(e['phi_deg'])   for e in log)
    accel_max = max(abs(e['accel_meas']) for e in log)
    final_steps    = log[-1]['steps']
    expected_steps = sum(e['step_rate'] * DT_S for e in log)
    step_loss      = abs(final_steps - expected_steps)

    print(f"\n  Summary — {name}")
    print(f"    Max pendulum deflection : {phi_max:.2f}°")
    print(f"    Max inferred arm accel  : {accel_max:.1f} rad/s²")
    print(f"    Final step count        : {final_steps}")
    print(f"    Expected from integral  : {expected_steps:.0f}")
    verdict = 'OK' if step_loss < 5 else 'WARNING — steps skipped!'
    print(f"    Estimated step loss     : {step_loss:.0f} steps  [{verdict}]")

# ── Run test suite ─────────────────────────────────────────────────

# A: Gentle ramp — baseline
log_a = run_profile("A: Gentle ramp  (0 → 300 steps/s, accel=2000)",
    [(300, 600), (0, 600)], max_accel=2000)
time.sleep_ms(1500)

# B: Nominal — what the controller uses
log_b = run_profile("B: Nominal ramp  (0 → 600 steps/s, accel=4000)",
    [(600, 400), (0, 400)], max_accel=4000)
time.sleep_ms(1500)

# C: Aggressive — find stall threshold
log_c = run_profile("C: Aggressive ramp  (0 → 800 steps/s, accel=8000)",
    [(800, 300), (0, 300)], max_accel=8000)
time.sleep_ms(1500)

# D: Direction reversal
log_d = run_profile("D: Reversal  (300 → -300 steps/s)",
    [(300, 400), (-300, 400), (0, 400)], max_accel=4000)
time.sleep_ms(1500)

# E: Settling — pendulum ring-down after stop
log_e = run_profile("E: Settling after stop  (400 → 0, watch ring-down)",
    [(400, 600), (0, 1200)], max_accel=6000)

# ── Print summaries ────────────────────────────────────────────────
print(f"\n{'═'*60}")
print("  RESULTS")
print(f"{'═'*60}")
for log, name in [(log_a,'A'),(log_b,'B'),(log_c,'C'),(log_d,'D'),(log_e,'E')]:
    analyse(log, name)

print(f"\n{'─'*60}")
print("  INTERPRETATION")
print("  If Test C shows step_loss > 5: reduce MAX_STEP_ACCEL in main.py")
print("  If Test B phi deflection is ~0: arm may not be moving (check EN)")
print("  Test E ring frequency should match ωₙ ≈ 1.84 Hz (period ~0.54 s)")
print("  If ring frequency differs: update pendulum length in feasibility tracker")
print(f"{'─'*60}")
