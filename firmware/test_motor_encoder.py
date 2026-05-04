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
from array import array

STEP_PIN = Pin(2, Pin.OUT)
DIR_PIN  = Pin(3, Pin.OUT)
EN_PIN   = Pin(4, Pin.OUT)
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400_000)

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
    """Run a step rate profile and print live telemetry.

    MicroPython heap is small on RP2040; avoid storing per-sample logs.
    Returns a small summary tuple (constant memory).
    For profiles that include a stop-and-ringdown segment, also returns an
    estimated ringdown frequency (Hz) computed from a small fixed-memory buffer.
    """
    global step_rate, step_accum, step_count
    step_rate = 0.0; step_accum = 0.0; step_count = 0
    t_total = 0

    # Summary stats (constant memory)
    phi_max_abs_deg = 0.0
    accel_max_abs   = 0.0
    expected_steps  = 0.0

    # Optional ringdown capture (fixed memory)
    ring_hz = None
    capture_ringdown = False
    capture_armed = False
    capture_decimate = 5               # capture every 5 samples = 10 ms at DT_MS=2
    capture_countdown = 0
    ring_phi_cdeg = array('h')         # centi-degrees
    ring_dt_s = (DT_MS / 1000.0) * capture_decimate
    prev_target_rate = 0.0

    print(f"\n{'─'*60}")
    print(f"  {name}")
    print(f"{'─'*60}")
    print(f"  {'t_ms':>5}  {'target':>7}  {'actual_rate':>11}  {'φ_deg':>7}  {'θ̈_arm':>12}  {'steps':>7}")

    motor_enable()

    for (target_rate, dur_ms) in profile:
        # Arm ringdown capture when we enter a 0-rate segment after motion.
        # Actual capture begins only once the *measured* step_rate has settled near 0.
        if (target_rate == 0) and (prev_target_rate != 0):
            capture_armed = True
            capture_ringdown = False
        prev_target_rate = target_rate

        for _ in range(dur_ms // DT_MS):
            t0  = time.ticks_us()
            phi = read_phi_rad()

            a_tan      = 9.81 * math.tan(phi)         # tangential accel (m/s²)
            theta_ddot = a_tan / ARM_LENGTH_M          # arm angular accel (rad/s²)

            update_stepper(target_rate, DT_S, max_accel)

            # Start ringdown capture only after the motor has actually stopped.
            if capture_armed and (not capture_ringdown) and (abs(step_rate) < 2.0):
                capture_ringdown = True
                capture_armed = False
                capture_countdown = 0
                ring_phi_cdeg = array('h')

            phi_deg = math.degrees(phi)
            abs_phi_deg = abs(phi_deg)
            if abs_phi_deg > phi_max_abs_deg:
                phi_max_abs_deg = abs_phi_deg

            abs_accel = abs(theta_ddot)
            if abs_accel > accel_max_abs:
                accel_max_abs = abs_accel

            # Integral of actual step_rate over time (same as old analyse())
            expected_steps += step_rate * DT_S

            # Ringdown capture (decimated)
            if capture_ringdown:
                if capture_countdown == 0:
                    # Store centi-degrees, clamped to int16 range
                    v = int(phi_deg * 100)
                    if v > 32767:
                        v = 32767
                    elif v < -32768:
                        v = -32768
                    ring_phi_cdeg.append(v)
                capture_countdown = (capture_countdown + 1) % capture_decimate

            if t_total % 100 == 0:
                print(f"  {t_total:5d}  {target_rate:7.0f}  {step_rate:11.1f}  "
                      f"{phi_deg:7.2f}°  {theta_ddot:+10.1f} r/s²  {step_count:7d}")

            t_total += DT_MS
            elapsed  = time.ticks_diff(time.ticks_us(), t0)
            time.sleep_us(max(0, DT_MS * 1000 - elapsed))

    motor_disable()

    # Estimate ringdown frequency from captured samples (if any)
    # Use a detrended rising zero-crossing method (works with DC offset and negative angles).
    if len(ring_phi_cdeg) >= 12:
        n = len(ring_phi_cdeg)
        s = 0
        for i in range(n):
            s += ring_phi_cdeg[i]
        mean_cdeg = s / n

        # Adaptive threshold based on observed oscillation amplitude
        min_v =  1e9
        max_v = -1e9
        for i in range(n):
            v = ring_phi_cdeg[i] - mean_cdeg
            if v < min_v:
                min_v = v
            if v > max_v:
                max_v = v
        amp_cdeg = max_v - min_v
        # Use 10% of amplitude, but never below 0.05°
        thresh_cdeg = amp_cdeg * 0.10
        if thresh_cdeg < 5:
            thresh_cdeg = 5

        prev = ring_phi_cdeg[0] - mean_cdeg
        last_rise_idx = -1
        sum_period_s = 0.0
        periods = 0

        for i in range(1, n):
            cur = ring_phi_cdeg[i] - mean_cdeg

            # Rising zero-crossing: prev < 0 and cur >= 0
            if (prev < 0) and (cur >= 0) and (abs(prev) >= thresh_cdeg or abs(cur) >= thresh_cdeg):
                if last_rise_idx >= 0:
                    sum_period_s += (i - last_rise_idx) * ring_dt_s
                    periods += 1
                last_rise_idx = i

            prev = cur

        if periods > 0:
            period_s = sum_period_s / periods
            if period_s > 0:
                ring_hz = 1.0 / period_s

    return (phi_max_abs_deg, accel_max_abs, step_count, expected_steps, ring_hz)

def print_summary(summary, label):
    phi_max_deg, accel_max, final_steps, expected_steps, ring_hz = summary
    step_loss = abs(final_steps - expected_steps)

    print(f"\n  Summary — {label}")
    print(f"    Max pendulum deflection : {phi_max_deg:.2f}°")
    print(f"    Max inferred arm accel  : {accel_max:.1f} rad/s²")
    print(f"    Final step count        : {final_steps}")
    print(f"    Expected from integral  : {expected_steps:.0f}")
    verdict = 'OK' if step_loss < 5 else 'WARNING — steps skipped!'
    print(f"    Estimated step loss     : {step_loss:.0f} steps  [{verdict}]")
    if ring_hz is not None:
        print(f"    Ringdown frequency est. : {ring_hz:.2f} Hz")

# ── Run test suite ─────────────────────────────────────────────────

# A: Gentle ramp — baseline
sum_a = run_profile("A: Gentle ramp  (0 → 300 steps/s, accel=2000)",
    [(300, 600), (0, 600)], max_accel=(5120000//4))
time.sleep_ms(1500)

# B: Nominal — what the controller uses
sum_b = run_profile("B: Nominal ramp  (0 → 600 steps/s, accel=4000)",
    [(600, 400), (0, 400)], max_accel=(5120000//2))
time.sleep_ms(1500)

# C: Aggressive — find stall threshold
sum_c = run_profile("C: Aggressive ramp  (0 → 800 steps/s, accel=8000)",
    [(800, 300), (0, 300)], max_accel=5120000)
time.sleep_ms(1500)

# D: Direction reversal
sum_d = run_profile("D: Reversal  (300 → -300 steps/s)",
    [(300, 400), (-300, 400), (0, 400)], max_accel=(5120000//2))
time.sleep_ms(1500)

# E: Settling — pendulum ring-down after stop
sum_e = run_profile("E: Settling after stop  (400 → 0, watch ring-down)",
    [(800, 700), (0, 2000)], max_accel=(5120000//2))

# ── Print summaries ────────────────────────────────────────────────
print(f"\n{'═'*60}")
print("  RESULTS")
print(f"{'═'*60}")
for summary, label in [(sum_a,'A'),(sum_b,'B'),(sum_c,'C'),(sum_d,'D'),(sum_e,'E')]:
    print_summary(summary, label)

print(f"\n{'─'*60}")
print("  INTERPRETATION")
print("  If Test C shows step_loss > 5: reduce MAX_STEP_ACCEL in main.py")
print("  If Test B phi deflection is ~0: arm may not be moving (check EN)")
# if sum_e[4] is not None:
#     print(f"  Test E ring frequency: measured ≈ {sum_e[4]:.2f} Hz (expected ωₙ ≈ 1.84 Hz)")
# else:
#     print("  Test E ring frequency: could not estimate (ringdown too small/damped; try larger step rate or lower threshold)")
# print("  If ring frequency differs: update pendulum length in feasibility tracker")
print(f"{'─'*60}")
