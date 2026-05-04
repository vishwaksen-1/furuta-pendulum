# main.py
# Furuta Pendulum — Main Balance Controller
# Hardware: RPi Pico + 17HS4401S + A4988 + AS5600
#
# Supports multiple control strategies: PD, LQR, NL-P, NL-Full
# Select strategy and parameters below.
#
# BEFORE RUNNING:
#   1. Run all tests in firmware/test/ directory
#   2. Set ZERO_RAW from test/test_encoder.py
#   3. Choose control strategy and start with conservative gains
#   4. Follow tuning guide in docs/05_tuning_guide.md
#   5. Always hold pendulum upright before activating

from machine import Pin, I2C
import time, math

# Import common hardware and control modules
import control_lib as lib
from control_strategies import get_controller

# ─────────────────────────────────────────────
#  CONTROL STRATEGY SELECTION
# ─────────────────────────────────────────────
# Choose one strategy:
#   "pd"       → Traditional PD (2D feedback: φ, φ̇)
#   "lqr"      → Optimal LQR (4D feedback: φ, φ̇, θ, θ̇)
#   "nl-p"     → Nonlinear P only (log on proportional term)
#   "nl-full"  → Nonlinear full PD (log on entire PD feedback)
CONTROL_STRATEGY = "pd"

# Strategy-specific parameters
CONTROL_PARAMS = {
    # PD parameters (used when CONTROL_STRATEGY="pd")
    "kp": 150.0,
    "kd": 42.0,
    
    # LQR gains (used when CONTROL_STRATEGY="lqr")
    # Conservative: Q=diag(100,10,10,1), R=0.1
    "k_lqr": [150.0, 42.0, 6.0, 2.0],
    
    # Nonlinear parameters (used when CONTROL_STRATEGY="nl-p" or "nl-full")
    "k1": 0.03,     # log scaling parameter (avoids log(0))
    
    # Common
    "k_center": 6.0,
    "alpha_max": 600.0,
}

# ─────────────────────────────────────────────
#  CALIBRATION
# ─────────────────────────────────────────────
ZERO_RAW = 1750    # raw AS5600 count when pendulum is upright
               # (update from test/test_encoder.py after calibration)

# ─────────────────────────────────────────────
#  CONTROLLER PARAMETERS
# ─────────────────────────────────────────────
DT_S           = 0.002          # 500 Hz control loop
DT_US          = 2000           # microseconds

ALPHA_EMA      = 0.8            # velocity EMA smoothing
N_DIFF         = 3              # finite difference window

MAX_STEP_RATE  = 8000.0         # steps/s ceiling
MAX_STEP_ACCEL = 5120000.0/8    # steps/s² ramp limit

THETA_SOFT_RAD = math.radians(90)   # arm soft limit (centering ramps up)
THETA_HARD_RAD = math.radians(120)  # arm hard limit (motor disabled)
PHI_CUTOFF_RAD = math.radians(75)   # pendulum fall threshold
PHI_ACTIVE_RAD = math.radians(30)   # pendulum angle to activate

THETA_ZERO_TOL_RAD = math.radians(2)  # consider arm centered within this

# ─────────────────────────────────────────────
#  RUNTIME STATE
# ─────────────────────────────────────────────
state          = lib.IDLE
phi_history    = [0.0] * (N_DIFF + 2)
phi_dot_filt   = 0.0
idle_timer_ms  = 0.0

# Controller instance
controller = None

# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
def main():
    global state, phi_history, phi_dot_filt, idle_timer_ms, controller
    global lib

    print("=" * 50)
    print("  Furuta Pendulum — Balance Controller")
    print("  IIT Kharagpur — EECE Design Lab")
    print("=" * 50)
    print(f"  Strategy: {CONTROL_STRATEGY.upper()}")
    print(f"  Loop: {int(1/DT_S)} Hz")
    print()

    # Initialize controller
    try:
        controller = get_controller(
            CONTROL_STRATEGY,
            kp=CONTROL_PARAMS.get("kp"),
            kd=CONTROL_PARAMS.get("kd"),
            k_lqr=CONTROL_PARAMS.get("k_lqr"),
            k_center=CONTROL_PARAMS.get("k_center"),
            alpha_max=CONTROL_PARAMS.get("alpha_max")
        )
        print(f"  Controller: {controller}")
    except Exception as e:
        print(f"ERROR: Failed to initialize controller: {e}")
        return

    # Check magnet
    if not lib.check_magnet():
        print("FAULT: AS5600 magnet not detected.")
        print("       Check magnet gap and orientation. Exiting.")
        state = lib.FAULT
        return

    # Calibration
    zero_raw_cal = lib.calibrate_zero_interactive()
    global ZERO_RAW
    ZERO_RAW = zero_raw_cal

    phi_now    = lib.read_phi(ZERO_RAW)
    phi_history = [phi_now] * (N_DIFF + 2)

    lib.motor_disable()
    print(f"State: IDLE")
    print(f"Hold pendulum upright (within {math.degrees(PHI_ACTIVE_RAD):.0f}°) to activate.\n")

    loop_count  = 0
    print_every = 100   # status every ~200 ms

    while True:
        t_start = time.ticks_us()

        # ── 1. READ SENSOR ──────────────────────────
        try:
            phi = lib.read_phi(ZERO_RAW)
        except Exception:
            state = lib.FAULT
            lib.motor_disable()
            print("FAULT: I2C read error. Stopping.")
            break

        # ── 2. VELOCITY ESTIMATE ────────────────────
        phi_history    = [phi] + phi_history[:-1]
        phi_dot_filt, theta_dot = lib.estimate_velocities(
            phi_history, phi_dot_filt, lib.step_rate, DT_S, N_DIFF, ALPHA_EMA
        )

        # ── 3. ARM ANGLE ────────────────────────────
        theta = lib.step_count * lib.RAD_PER_STEP

        # ── 4. STATE MACHINE ────────────────────────
        if state == lib.IDLE:
            lib.motor_disable()
            if abs(phi) < PHI_ACTIVE_RAD:
                idle_timer_ms += DT_S * 1000
                if idle_timer_ms >= 500:
                    state         = lib.ACTIVE
                    lib.step_count = 0
                    lib.step_rate  = 0.0
                    lib.step_accum = 0.0
                    idle_timer_ms  = 0.0
                    lib.motor_enable()
                    print(">>> ACTIVE — balancing")
            else:
                idle_timer_ms = 0

        elif state == lib.ACTIVE:
            if abs(phi) > PHI_CUTOFF_RAD:
                state = lib.RECOVERING
                lib.motor_disable()
                idle_timer_ms = 0.0
                print(f">>> RECOVERING — φ = {math.degrees(phi):.1f}° (> 75°)")
            elif abs(theta) > THETA_HARD_RAD:
                state = lib.LIMIT_HIT
                idle_timer_ms = 0.0
                lib.step_rate  = 0.0
                lib.step_accum = 0.0
                print(f">>> LIMIT_HIT — unwinding to 0°")
            else:
                # Compute control command
                centering_mult = lib.centering_ramp(
                    theta, THETA_SOFT_RAD, THETA_HARD_RAD
                )
                u = controller.compute_control(
                    phi, phi_dot_filt, theta, theta_dot, centering_mult
                )

                # Convert control command to step rate target
                target_step_rate = lib.step_rate + u * DT_S * lib.STEPS_PER_REV / (2 * math.pi)
                lib.update_stepper(target_step_rate, DT_S, MAX_STEP_RATE, MAX_STEP_ACCEL)

        elif state == lib.RECOVERING:
            lib.motor_disable()
            if abs(phi) < PHI_ACTIVE_RAD:
                idle_timer_ms += DT_S * 1000
                if idle_timer_ms >= 500:
                    state         = lib.ACTIVE
                    lib.step_count = 0
                    lib.step_rate  = 0.0
                    lib.step_accum = 0.0
                    idle_timer_ms  = 0.0
                    lib.motor_enable()
                    print(">>> ACTIVE — recovered")
            else:
                idle_timer_ms = 0

        elif state == lib.LIMIT_HIT:
            lib.motor_enable()
            if abs(theta) <= THETA_ZERO_TOL_RAD:
                lib.step_count = 0
                lib.step_rate  = 0.0
                lib.step_accum = 0.0
                idle_timer_ms  = 0.0
                state = lib.RECOVERING
                print(">>> UNWIND COMPLETE — waiting for human reset")
            else:
                # Drive back toward zero
                target_step_rate = math.copysign(2000.0, -theta)
                lib.update_stepper(target_step_rate, DT_S, MAX_STEP_RATE, MAX_STEP_ACCEL)

        elif state == lib.FAULT:
            lib.motor_disable()
            break

        # ── 5. STATUS OUTPUT ────────────────────────
        loop_count += 1
        if loop_count % print_every == 0:
            if state == lib.ACTIVE:
                centering_mult = lib.centering_ramp(
                    theta, THETA_SOFT_RAD, THETA_HARD_RAD
                )
                u_display = controller.compute_control(
                    phi, phi_dot_filt, theta, theta_dot, centering_mult
                )
            else:
                u_display = 0.0
            print(f"[{lib.STATE_NAMES[state]:10s}] "
                  f"φ={math.degrees(phi):+6.2f}°  "
                  f"φ̇={math.degrees(phi_dot_filt):+7.1f}°/s  "
                  f"θ={math.degrees(theta):+6.1f}°  "
                  f"rate={lib.step_rate:+6.0f}  "
                  f"u={u_display:+5.0f}")

        # ── 6. LOOP TIMING ──────────────────────────
        elapsed   = time.ticks_diff(time.ticks_us(), t_start)
        remaining = DT_US - elapsed
        if remaining > 0:
            time.sleep_us(remaining)

# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        lib.motor_disable()
        print("\nStopped by user. Motor disabled.")
