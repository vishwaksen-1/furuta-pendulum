# motor_speed_test.py
# Standalone speed/limit test for 17HS4401S + A4988 + RPi Pico
# No encoder needed. Motor + driver wired per hardware/wiring_diagram.md
#
# Tests run automatically in sequence. Watch the motor and listen.
# Results printed over USB serial (115200 baud, Thonny shell or screen).
#
# WIRING REMINDER (from wiring_diagram.md):
#   GP2 → STEP,  GP3 → DIR,  GP4 → ENABLE (active LOW)
#   MS1 → 3V3 (HIGH),  MS2 → 3V3 (HIGH),  MS3 → GND (LOW)  → 1/8 step
#   VMOT → 12V,  100µF cap across VMOT/GND close to A4988
#   A4988 Vref set to 0.56V before running this

from machine import Pin, Timer
import time, math

# ─────────────────────────────────────────────
#  PINS
# ─────────────────────────────────────────────
STEP_PIN = Pin(2, Pin.OUT)
DIR_PIN  = Pin(3, Pin.OUT)
EN_PIN   = Pin(4, Pin.OUT)

STEPS_PER_REV = 1600      # 200 base × 8 microsteps

def enable():
    EN_PIN.value(0)        # active LOW

def disable():
    EN_PIN.value(1)

# ─────────────────────────────────────────────
#  PRIMITIVE: blocking step burst
#  Used for simple fixed-rate tests.
#  step_delay_us = half-period of STEP pulse.
#  full period = 2 × step_delay_us
#  step rate (steps/s) = 1_000_000 / (2 × step_delay_us)
# ─────────────────────────────────────────────
def run_steps(n_steps, direction, step_delay_us):
    DIR_PIN.value(direction)
    time.sleep_us(5)                       # A4988 DIR setup time
    for _ in range(n_steps):
        STEP_PIN.value(1)
        time.sleep_us(step_delay_us)
        STEP_PIN.value(0)
        time.sleep_us(step_delay_us)

# ─────────────────────────────────────────────
#  RAMP: accelerate from start_rate to end_rate
#  over n_steps steps, then hold end_rate for
#  hold_steps steps.
#  All rates in steps/s.
# ─────────────────────────────────────────────
def run_ramp(start_rate, end_rate, n_steps, direction=1, hold_steps=0):
    DIR_PIN.value(direction)
    time.sleep_us(5)

    if n_steps <= 0:
        return

    for i in range(n_steps):
        # Linearly interpolate step rate
        rate = start_rate + (end_rate - start_rate) * i / n_steps
        rate = max(rate, 10)              # never go below 10 steps/s
        delay_us = int(500_000 / rate)   # half-period in µs
        STEP_PIN.value(1)
        time.sleep_us(delay_us)
        STEP_PIN.value(0)
        time.sleep_us(delay_us)

    if hold_steps > 0 and end_rate > 0:
        delay_us = int(500_000 / end_rate)
        for _ in range(hold_steps):
            STEP_PIN.value(1)
            time.sleep_us(delay_us)
            STEP_PIN.value(0)
            time.sleep_us(delay_us)

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def rate_to_rpm(steps_per_sec):
    return steps_per_sec / STEPS_PER_REV * 60.0

def rate_to_delay(steps_per_sec):
    return int(500_000 / steps_per_sec)

def separator(char='─', width=54):
    print(char * width)

def header(text):
    separator('═')
    print(f"  {text}")
    separator('═')

def subheader(text):
    separator()
    print(f"  {text}")
    separator()

def prompt_continue(msg="Press ENTER to run next test..."):
    try:
        input(f"\n  {msg}\n")
    except Exception:
        time.sleep_ms(800)

# ─────────────────────────────────────────────
#  TEST A — Fixed-rate sweep
#  Runs at discrete step rates from slow to fast.
#  At each rate: 1 full revolution CW, pause, 1 rev CCW.
#  Listen/watch for stall, resonance, missed steps.
# ─────────────────────────────────────────────
def test_a_fixed_rate_sweep():
    subheader("TEST A — Fixed-Rate Sweep")
    print("  One revolution at each rate, CW then CCW.")
    print("  Listen for stall or resonance. Note the last rate that runs clean.\n")

    rates = [50, 100, 150, 200, 250, 300, 400, 500, 600, 700, 800,
             900, 1000, 1100, 1200, 1400, 1600, 1800, 2000]

    print(f"  {'Rate (steps/s)':>15}  {'RPM':>7}  {'Delay µs':>10}  Result")
    separator()

    last_clean = 0
    for rate in rates:
        rpm      = rate_to_rpm(rate)
        delay_us = rate_to_delay(rate)

        enable()
        time.sleep_ms(50)

        # CW revolution
        run_steps(STEPS_PER_REV, direction=1, step_delay_us=delay_us)
        time.sleep_ms(150)
        # CCW back
        run_steps(STEPS_PER_REV, direction=0, step_delay_us=delay_us)
        time.sleep_ms(300)

        disable()

        print(f"  {rate:>15d}  {rpm:>7.1f}  {delay_us:>10d}  <- observe")
        time.sleep_ms(500)

    print(f"\n  Note the last rate where motor ran without audible stall.")
    print(f"  That is your practical MAX_STEP_RATE for main.py.")

# ─────────────────────────────────────────────
#  TEST B — Acceleration limit finder
#  Ramps from rest to a target speed over varying
#  distances. Short ramp = aggressive acceleration.
#  Find the shortest ramp that doesn't stall.
# ─────────────────────────────────────────────
def test_b_accel_limit():
    subheader("TEST B — Acceleration Limit")
    print("  Ramps from 0 to 800 steps/s over varying ramp lengths.")
    print("  Shorter ramp = higher acceleration.")
    print("  Motor stall or loud clunk = ramp too short (accel too high).\n")

    target_rate  = 800    # steps/s target speed
    hold_steps   = 400    # steps to hold at target before stopping

    # Ramp lengths to test (in steps)
    # Longer = gentler acceleration
    ramp_lengths = [20, 40, 80, 120, 200, 300, 500]

    print(f"  {'Ramp steps':>12}  {'Accel (steps/s²)':>18}  Result")
    separator()

    for ramp_len in ramp_lengths:
        # Effective acceleration = Δrate / time = Δrate / (ramp_len / avg_rate)
        avg_rate = target_rate / 2
        ramp_time_s = ramp_len / avg_rate
        accel = target_rate / ramp_time_s

        enable()
        time.sleep_ms(50)

        run_ramp(50, target_rate, ramp_len, direction=1, hold_steps=hold_steps)
        time.sleep_ms(100)
        run_ramp(target_rate, 50, ramp_len, direction=1)  # decel back
        time.sleep_ms(100)
        run_steps(STEPS_PER_REV // 4, direction=0, step_delay_us=rate_to_delay(200))  # return

        disable()
        time.sleep_ms(600)

        print(f"  {ramp_len:>12d}  {accel:>18.0f}  <- observe")

    print(f"\n  Shortest ramp with clean run → use that accel in main.py MAX_STEP_ACCEL.")
    print(f"  Formula: MAX_STEP_ACCEL = target_rate / ramp_time")

# ─────────────────────────────────────────────
#  TEST C — Resonance scan
#  Steps at very slow rates where NEMA 17 motors
#  notoriously resonate (mid-band instability).
#  Identifies the "rough" speed range to avoid.
# ─────────────────────────────────────────────
def test_c_resonance_scan():
    subheader("TEST C — Resonance / Mid-band Scan")
    print("  Slow sweep through 50–400 steps/s.")
    print("  At some rates the motor will vibrate, sound rough, or stall.")
    print("  These are resonance zones — avoid commanding these rates in main.py.\n")

    print(f"  {'Rate (steps/s)':>15}  {'RPM':>7}  Observe")
    separator()

    # Fine-grained sweep through the typical resonance band
    rates = list(range(50, 410, 10))

    enable()
    time.sleep_ms(100)

    for rate in rates:
        rpm      = rate_to_rpm(rate)
        delay_us = rate_to_delay(rate)

        # Run for 0.5 revolution at this rate
        run_steps(STEPS_PER_REV // 2, direction=1, step_delay_us=delay_us)

        if rate % 50 == 0:
            print(f"  {rate:>15d}  {rpm:>7.1f}  <- now")

        time.sleep_ms(30)

    # Return home
    run_ramp(50, 300, 100, direction=0)
    run_steps(STEPS_PER_REV * len(rates) // 2 % STEPS_PER_REV,
              direction=0, step_delay_us=rate_to_delay(200))

    disable()
    print(f"\n  Rough/noisy speed bands should be noted and avoided.")
    print(f"  Microstepping (1/8) reduces resonance vs full step, but doesn't eliminate it.")

# ─────────────────────────────────────────────
#  TEST D — Direction reversal stress test
#  Repeatedly reverses at various speeds.
#  Reveals whether the motor can track rapid
#  sign changes (what the controller does constantly).
# ─────────────────────────────────────────────
def test_d_reversal():
    subheader("TEST D — Direction Reversal Stress Test")
    print("  Alternates direction at increasing speeds.")
    print("  Motor must start, stop, reverse cleanly each time.")
    print("  Stall or clunk = this reversal speed is too high.\n")

    reversal_rates  = [200, 300, 400, 500, 600, 700, 800]
    steps_per_burst = STEPS_PER_REV // 4   # quarter revolution per direction

    print(f"  {'Rate (steps/s)':>15}  {'RPM':>7}  {'Reversals':>10}  Result")
    separator()

    for rate in reversal_rates:
        rpm      = rate_to_rpm(rate)
        delay_us = rate_to_delay(rate)
        n_reversals = 6

        enable()
        time.sleep_ms(50)

        stall_detected = False
        t_start = time.ticks_ms()

        for rev in range(n_reversals):
            direction = rev % 2
            run_steps(steps_per_burst, direction=direction, step_delay_us=delay_us)
            time.sleep_ms(20)   # brief pause at reversal point

        t_elapsed = time.ticks_diff(time.ticks_ms(), t_start)

        disable()
        time.sleep_ms(500)

        # Theoretical time for n_reversals × steps_per_burst steps at this rate
        expected_ms = int(n_reversals * steps_per_burst / rate * 1000)
        timing_ok   = abs(t_elapsed - expected_ms) < expected_ms * 0.15

        result = "clean" if timing_ok else "check timing"
        print(f"  {rate:>15d}  {rpm:>7.1f}  {n_reversals:>10d}  {result}")

    print(f"\n  The controller reverses direction constantly during balancing.")
    print(f"  Highest rate that runs clean = safe ceiling for controller reversals.")

# ─────────────────────────────────────────────
#  TEST E — Absolute top speed
#  Ramps up gently to high rates to find where
#  the motor simply can't keep up anymore.
#  Uses a long ramp so acceleration isn't the limit.
# ─────────────────────────────────────────────
def test_e_top_speed():
    subheader("TEST E — Absolute Top Speed (Long Ramp)")
    print("  Slowly ramps up to find absolute speed ceiling.")
    print("  Motor will stall, lose sync, or sound wrong at the limit.")
    print("  This is the hardware ceiling — not safe for control use.\n")

    # Ramp from 100 to 3000 steps/s over 3000 steps (very gentle accel)
    # then hold each century for a moment to listen
    milestones = list(range(100, 3100, 100))

    print(f"  {'Rate (steps/s)':>15}  {'RPM':>7}  Status")
    separator()

    enable()
    time.sleep_ms(100)

    current_rate = 100
    alive = True

    for target in milestones:
        if not alive:
            break

        # Ramp from current to target over 200 steps
        run_ramp(current_rate, target, 200, direction=1)

        # Hold at target for half a revolution
        hold_delay = rate_to_delay(target)
        run_steps(STEPS_PER_REV // 2, direction=1, step_delay_us=hold_delay)

        rpm = rate_to_rpm(target)
        print(f"  {target:>15d}  {rpm:>7.1f}  <- running")

        current_rate = target
        time.sleep_ms(50)

    # Ramp back down safely
    run_ramp(current_rate, 100, 500, direction=1)
    run_steps(200, direction=0, step_delay_us=rate_to_delay(100))

    disable()
    print(f"\n  Last rate before stall/roughness = absolute hardware ceiling.")
    print(f"  Recommended MAX_STEP_RATE for control = 60–70% of that ceiling.")

# ─────────────────────────────────────────────
#  TEST F — Holding torque check
#  Enables motor at rest and lets you push the arm
#  by hand. Subjective feel for holding force.
# ─────────────────────────────────────────────
def test_f_holding_torque():
    subheader("TEST F — Holding Torque (Manual)")
    print("  Motor enabled, no steps. Try to rotate arm by hand.")
    print("  Should resist firmly. If it gives easily, Vref is too low.")
    print("  Motor will stay enabled for 10 seconds.\n")

    enable()
    print("  Motor ENABLED — push the arm now...")

    for i in range(10, 0, -1):
        print(f"  {i}...")
        time.sleep_ms(1000)

    disable()
    print("  Motor DISABLED.\n")
    print("  If arm moved easily: increase Vref toward 0.70V")
    print("  If motor was hot after 10s: Vref may be too high — check 0.56V target")

# ─────────────────────────────────────────────
#  MAIN — Run all tests in sequence
# ─────────────────────────────────────────────
def main():
    header("17HS4401S Motor Speed & Limit Test")
    print("  Pico + A4988,  1/8 microstepping,  1600 steps/rev")
    print("  Vref should be set to 0.56V before running.")
    print("  Watch and listen to the motor during each test.\n")
    print("  Tests will run one at a time.")
    print("  Press ENTER between tests to continue.")
    print("  Press Ctrl+C at any time to stop.\n")
    separator()

    try:
        prompt_continue("Press ENTER to begin TEST A — Fixed Rate Sweep")
        test_a_fixed_rate_sweep()

        prompt_continue("Press ENTER for TEST B — Acceleration Limit")
        test_b_accel_limit()

        prompt_continue("Press ENTER for TEST C — Resonance Scan")
        test_c_resonance_scan()

        prompt_continue("Press ENTER for TEST D — Reversal Stress Test")
        test_d_reversal()

        prompt_continue("Press ENTER for TEST E — Absolute Top Speed")
        test_e_top_speed()

        prompt_continue("Press ENTER for TEST F — Holding Torque (manual)")
        test_f_holding_torque()

        header("ALL TESTS COMPLETE")
        print("  Fill in your results below and update main.py:\n")
        print("  MAX_STEP_RATE  = ___  steps/s   (Test A: last clean rate × 0.85)")
        print("  MAX_STEP_ACCEL = ___  steps/s²  (Test B: shortest clean ramp accel × 0.80)")
        print("  Resonance zone = ___  –  ___ steps/s  (Test C: avoid in control loop)")
        print("  Top speed      = ___  steps/s   (Test E: informational only)")
        separator()

    except KeyboardInterrupt:
        disable()
        print("\n\nStopped by user. Motor disabled.")

main()