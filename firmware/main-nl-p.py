# main.py
# Furuta Pendulum — Main Balancing Controller
# Hardware: RPi Pico + 17HS4401S + A4988 + AS5600
#
# BEFORE RUNNING:
#   1. Complete all 6 tests in firmware/test_*.py
#   2. Set ZERO_RAW to the value from test_encoder.py
#   3. Start with CONSERVATIVE gains (default below)
#   4. Follow tuning procedure in docs/05_tuning_guide.md
#   5. Always hold pendulum upright before the script activates

from machine import Pin, I2C
import time, math

# ─────────────────────────────────────────────
#  HARDWARE PINS
# ─────────────────────────────────────────────
STEP_PIN = Pin(2, Pin.OUT)
DIR_PIN  = Pin(3, Pin.OUT)
EN_PIN   = Pin(4, Pin.OUT)
i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400_000)

# ─────────────────────────────────────────────
#  SYSTEM CONSTANTS
# ─────────────────────────────────────────────
AS5600_ADDR   = 0x36
STEPS_PER_REV = 1600           # 200 base × 8 microsteps (1/8 step)
RAD_PER_STEP  = 2*math.pi / STEPS_PER_REV
RAD_PER_COUNT = 2*math.pi / 4096

# ─────────────────────────────────────────────
#  CALIBRATION  ← set from test_encoder.py
# ─────────────────────────────────────────────
ZERO_RAW = 1750    # raw AS5600 count when pendulum is exactly upright

# ─────────────────────────────────────────────
#  CONTROL GAINS
#
#  Derived by pole placement (see docs/02_control_design.md):
#    Kp = (ωc² + ωₙ²) / B       where ωₙ = 11.57 rad/s, B = 0.955
#    Kd = 2·ζ·ωc / B             where ζ = 0.7
#
#  Gain sets — uncomment one to select:
# ─────────────────────────────────────────────

# smol
KP = 200.0;      KD = 42.0

# Conservative: ωc = 2.5×ωₙ  — start here
# KP = 940.0;    KD = 42.0

# Nominal: ωc = 3.5×ωₙ  — use once conservative works
# KP = 1858.0;  KD = 59.4

# Aggressive: ωc = 5.0×ωₙ  — only if nominal is too sluggish
# KP = 3638.0;  KD = 84.7

K_CENTER = 6    # arm centering gain [rad/s² per rad of arm displacement]

# ─────────────────────────────────────────────
#  CONTROLLER PARAMETERS
# ─────────────────────────────────────────────
DT_S           = 0.002          # 500 Hz control loop (seconds)
DT_US          = 2000           # same in microseconds

ALPHA_EMA      = 0.8           # velocity EMA smoothing (tune from test_velocity.py)
N_DIFF         = 3              # finite difference window (samples)

ALPHA_MAX      = 600.0          # max arm angular accel command [rad/s²]
MAX_STEP_RATE  = 8000.0          # max step rate [steps/s] — safe torque zone
MAX_STEP_ACCEL = 5120000.0/8         # step rate ramp limit [steps/s²]

UNWIND_STEP_RATE   = 7000.0        # [steps/s] fast unwind rate in LIMIT_HIT
THETA_ZERO_TOL_RAD = math.radians(2)  # [rad] consider arm "back to zero" within this

THETA_SOFT_RAD = math.radians(120)   # arm soft limit: centering ramps up
THETA_HARD_RAD = math.radians(170)   # arm hard stop: motor disabled
PHI_CUTOFF_RAD = math.radians(75)   # pendulum fall threshold → RECOVERING
PHI_ACTIVE_RAD = math.radians(30)    # must be within this to activate/recover

# ─────────────────────────────────────────────
#  STATE MACHINE
# ─────────────────────────────────────────────
IDLE       = 0    # motor off, waiting for upright
ACTIVE     = 1    # PD control running
RECOVERING = 2    # pendulum fell >15°, waiting for manual reset
LIMIT_HIT  = 3    # arm hit cable wrap limit
FAULT      = 4    # sensor error

STATE_NAMES = {0:"IDLE", 1:"ACTIVE", 2:"RECOVERING", 3:"LIMIT_HIT", 4:"FAULT"}

# ─────────────────────────────────────────────
#  RUNTIME STATE
# ─────────────────────────────────────────────
state          = IDLE
step_rate      = 0.0     # current step rate [steps/s, signed]
step_count     = 0       # arm position [steps from activation zero]
step_accum     = 0.0     # fractional step accumulator

phi_history    = [0.0] * (N_DIFF + 2)
phi_dot_filt   = 0.0
idle_timer_ms  = 0.0

# ─────────────────────────────────────────────
#  HARDWARE HELPERS
# ─────────────────────────────────────────────
def motor_enable():
    EN_PIN.value(0)

def motor_disable():
    global step_rate
    EN_PIN.value(1)
    step_rate = 0.0

def read_raw_count() -> int:
    """Read raw AS5600 count (0..4095)."""
    data = i2c.readfrom_mem(AS5600_ADDR, 0x0C, 2)
    return ((data[0] & 0x0F) << 8) | data[1]

def read_phi() -> float:
    """Read AS5600 and return pendulum angle in radians (0 = upright)."""
    raw   = read_raw_count()
    delta = raw - ZERO_RAW
    if delta >  2048: delta -= 4096
    if delta < -2048: delta += 4096
    return delta * RAD_PER_COUNT

def check_magnet() -> bool:
    # status = i2c.readfrom_mem(AS5600_ADDR, 0x0B, 1)[0]
    # return bool(status & 0x08)
    return True

def fire_steps(n: int):
    """Fire abs(n) step pulses. Sign of n sets direction."""
    global step_count
    if n == 0:
        return
    DIR_PIN.value(0 if n > 0 else 1)
    time.sleep_us(2)
    for _ in range(abs(n)):
        STEP_PIN.value(1)
        time.sleep_us(2)
        STEP_PIN.value(0)
        time.sleep_us(2)
    step_count += n

# ─────────────────────────────────────────────
#  STEP RATE CONTROLLER
# ─────────────────────────────────────────────
def update_stepper(target_rate: float, dt: float):
    """
    Ramp step_rate toward target_rate, limited by MAX_STEP_ACCEL.
    Fire accumulated steps. Returns steps fired this cycle.
    """
    global step_rate, step_accum

    max_delta = MAX_STEP_ACCEL * dt
    error     = target_rate - step_rate
    if abs(error) <= max_delta:
        step_rate = target_rate
    else:
        step_rate += math.copysign(max_delta, error)

    step_rate = max(-MAX_STEP_RATE, min(MAX_STEP_RATE, step_rate))

    step_accum += step_rate * dt
    steps = int(step_accum)
    step_accum -= steps

    fire_steps(steps)
    return steps

# ─────────────────────────────────────────────
#  CENTERING RAMP
# ─────────────────────────────────────────────
def centering_ramp(theta: float) -> float:
    """
    Returns centering gain multiplier.
    1× within soft limit, ramps 1→6× toward hard limit.
    """
    abs_theta = abs(theta)
    if abs_theta <= THETA_SOFT_RAD:
        return 1.0
    elif abs_theta <= THETA_HARD_RAD:
        frac = (abs_theta - THETA_SOFT_RAD) / (THETA_HARD_RAD - THETA_SOFT_RAD)
        return 1.0 + 5.0 * frac
    else:
        return 0.0   # past hard limit — handled by state machine

# ─────────────────────────────────────────────
#  CONTROL LAW
# ─────────────────────────────────────────────
def compute_control(phi: float, phi_dot: float, theta: float) -> float:
    """
    Returns commanded arm angular acceleration [rad/s²].
    Implements PD + arm centering with soft-limit ramp.
    """
    k1 = 0.03
    u_pd     = (KP * (phi))*(math.log(abs(phi)/k1 + 1)) + (KD * phi_dot)
    u_center = -K_CENTER * centering_ramp(theta) * theta
    u_total  = u_pd + u_center
    return max(-ALPHA_MAX, min(ALPHA_MAX, u_total))

# ─────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────
def main():
    global state, phi_history, phi_dot_filt, idle_timer_ms, step_count, ZERO_RAW, step_rate, step_accum

    print("=" * 50)
    print("  Furuta Pendulum — Balance Controller")
    print("  IIT Kharagpur — EECE Design Lab")
    print("=" * 50)
    print(f"  Kp={KP}, Kd={KD}, K_center={K_CENTER}")
    print(f"  Loop: {int(1/DT_S)} Hz,  Max step rate: {MAX_STEP_RATE} steps/s")
    print()

    if not check_magnet():
        print("FAULT: AS5600 magnet not detected.")
        print("       Check magnet gap and orientation. Exiting.")
        state = FAULT
        return

    # ── Startup zero calibration ─────────────────
    # Ask user to hold pendulum upright, then capture encoder count as ZERO_RAW.
    print("Hold the pendulum exactly upright, then press Enter to calibrate zero.")
    try:
        _ = input("Ready? ")
    except Exception:
        # If running in a non-interactive environment, keep the configured ZERO_RAW.
        print("(No stdin available — using configured ZERO_RAW.)")
    else:
        try:
            samples = 25
            sum_sin = 0.0
            sum_cos = 0.0
            for _ in range(samples):
                raw = read_raw_count()
                ang = raw * (2 * math.pi / 4096)
                sum_sin += math.sin(ang)
                sum_cos += math.cos(ang)
                time.sleep_ms(5)

            mean_ang = math.atan2(sum_sin, sum_cos)
            if mean_ang < 0:
                mean_ang += 2 * math.pi
            ZERO_RAW = int(round(mean_ang * 4096 / (2 * math.pi))) % 4096
            print(f"Calibrated ZERO_RAW = {ZERO_RAW}")
        except Exception:
            state = FAULT
            motor_disable()
            print("FAULT: I2C read error during calibration. Stopping.")
            return

    phi_now    = read_phi()
    phi_history = [phi_now] * (N_DIFF + 2)

    motor_disable()
    print(f"State: IDLE")
    print(f"Hold pendulum upright (within {math.degrees(PHI_ACTIVE_RAD):.0f}°) to activate.\n")

    loop_count  = 0
    print_every = 100   # status print every 100 loops = 200 ms

    while True:
        t_start = time.ticks_us()

        # ── 1. READ SENSOR ──────────────────────────
        try:
            phi = read_phi()
        except Exception:
            state = FAULT
            motor_disable()
            print("FAULT: I2C read error. Stopping.")
            break

        # ── 2. VELOCITY ESTIMATE ────────────────────
        phi_history    = [phi] + phi_history[:-1]
        phi_dot_raw    = (phi_history[0] - phi_history[N_DIFF]) / (N_DIFF * DT_S)
        phi_dot_filt   = ALPHA_EMA * phi_dot_raw + (1 - ALPHA_EMA) * phi_dot_filt

        # ── 3. ARM ANGLE ────────────────────────────
        theta = step_count * RAD_PER_STEP

        # ── 4. STATE MACHINE ────────────────────────
        if state == IDLE:
            motor_disable()
            if abs(phi) < PHI_ACTIVE_RAD:
                idle_timer_ms += DT_S * 1000
                if idle_timer_ms >= 500:
                    state         = ACTIVE
                    step_count    = 0      # zero arm position on activation
                    step_rate     = 0.0
                    step_accum    = 0.0
                    # phi_now       = read_phi()
                    # phi_history   = [phi_now] * (N_DIFF + 2)
                    # phi_dot_filt  = 0.0
                    idle_timer_ms = 0.0
                    motor_enable()
                    print(">>> ACTIVE — balancing")
            else:
                idle_timer_ms = 0

        elif state == ACTIVE:
            if abs(phi) > PHI_CUTOFF_RAD:
                state = RECOVERING
                motor_disable()
                idle_timer_ms = 0.0
                print(f">>> RECOVERING — φ = {math.degrees(phi):.1f}°  (> 75°)")
            elif abs(theta) > THETA_HARD_RAD:
                state = LIMIT_HIT
                idle_timer_ms = 0.0
                # Keep motor enabled to actively unwind back toward zero.
                step_rate  = 0.0
                step_accum = 0.0
                print(f">>> LIMIT_HIT — arm at {math.degrees(theta):.1f}° (unwinding to 0°)")
            else:
                # Normal control
                u = compute_control(phi, phi_dot_filt, theta)

                # u [rad/s²] → integrate to target step rate
                # target_step_rate = current_step_rate + u·dt·(steps/rad)
                target_step_rate = (step_rate + u * DT_S * STEPS_PER_REV / (2 * math.pi))
                update_stepper(target_step_rate, DT_S)

        elif state == RECOVERING:
            motor_disable()
            if abs(phi) < PHI_ACTIVE_RAD:
                idle_timer_ms += DT_S * 1000
                if idle_timer_ms >= 500:
                    state        = ACTIVE
                    step_count   = 0
                    step_rate     = 0.0
                    step_accum    = 0.0
                    # phi_now       = read_phi()
                    # phi_history   = [phi_now] * (N_DIFF + 2)
                    # phi_dot_filt  = 0.0
                    idle_timer_ms = 0.0
                    motor_enable()
                    print(">>> ACTIVE — recovered")
            else:
                idle_timer_ms = 0

        elif state == LIMIT_HIT:
                    # We hit the wire limit. The pendulum WILL fall. 
                    # Ignore the angle, drive to 0 safely, then go to RECOVERING.
                    motor_enable()

                    if abs(theta) <= THETA_ZERO_TOL_RAD:
                        # Arm is centered. Stop motor and wait for human to stand pendulum up.
                        step_count   = 0
                        step_rate    = 0.0
                        step_accum   = 0.0
                        idle_timer_ms = 0.0
                        state = RECOVERING
                        print(">>> UNWIND COMPLETE — waiting for human reset")
                    else:
                        # Drive back toward 0. Use 2000 steps/s (7000 is too violent for a hanging pendulum)
                        target_step_rate = math.copysign(2000.0, -theta)
                        update_stepper(target_step_rate, DT_S)

        elif state == FAULT:
            motor_disable()
            break

        # ── 5. STATUS OUTPUT ────────────────────────
        loop_count += 1
        if loop_count % print_every == 0:
            u_display = compute_control(phi, phi_dot_filt, theta) if state == ACTIVE else 0.0
            print(f"[{STATE_NAMES[state]:10s}] "
                  f"φ={math.degrees(phi):+6.2f}°  "
                  f"φ̇={math.degrees(phi_dot_filt):+7.1f}°/s  "
                  f"θ={math.degrees(theta):+6.1f}°  "
                  f"rate={step_rate:+6.0f}  "
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
        motor_disable()
        print("\nStopped by user. Motor disabled.")
