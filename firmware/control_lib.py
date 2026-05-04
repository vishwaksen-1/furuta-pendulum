# control_lib.py
# Common hardware and control helpers for Furuta Pendulum
# Used by main.py with different control strategies

from machine import Pin, I2C
import time, math

# ─────────────────────────────────────────────
#  HARDWARE PINS & I2C
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
#  MOTOR STATE
# ─────────────────────────────────────────────
step_rate  = 0.0
step_count = 0
step_accum = 0.0

def motor_enable():
    """Enable stepper motor."""
    EN_PIN.value(0)

def motor_disable():
    """Disable stepper motor and zero step rate."""
    global step_rate
    EN_PIN.value(1)
    step_rate = 0.0

def read_raw_count() -> int:
    """Read raw AS5600 count (0..4095)."""
    data = i2c.readfrom_mem(AS5600_ADDR, 0x0C, 2)
    return ((data[0] & 0x0F) << 8) | data[1]

def read_phi(zero_raw: int) -> float:
    """Read AS5600 and return pendulum angle in radians (0 = upright)."""
    raw   = read_raw_count()
    delta = raw - zero_raw
    if delta >  2048: delta -= 4096
    if delta < -2048: delta += 4096
    return delta * RAD_PER_COUNT

def check_magnet() -> bool:
    """Check if AS5600 magnet is detected."""
    return True  # Simplified; can add status register check if needed

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

def update_stepper(target_rate: float, dt: float, 
                   max_step_rate: float, max_step_accel: float) -> int:
    """
    Ramp step_rate toward target_rate, limited by max_step_accel.
    Fire accumulated steps. Returns steps fired this cycle.
    
    Args:
        target_rate: desired step rate in steps/s
        dt: time delta in seconds
        max_step_rate: maximum allowed step rate (steps/s)
        max_step_accel: maximum acceleration (steps/s²)
    """
    global step_rate, step_accum

    max_delta = max_step_accel * dt
    error     = target_rate - step_rate
    if abs(error) <= max_delta:
        step_rate = target_rate
    else:
        step_rate += math.copysign(max_delta, error)

    step_rate = max(-max_step_rate, min(max_step_rate, step_rate))

    step_accum += step_rate * dt
    steps = int(step_accum)
    step_accum -= steps

    fire_steps(steps)
    return steps

# ─────────────────────────────────────────────
#  VELOCITY ESTIMATION
# ─────────────────────────────────────────────
def estimate_velocities(phi_history: list, phi_dot_filt: float, 
                        step_rate: float, dt: float, 
                        n_diff: int, alpha_ema: float) -> tuple:
    """
    Estimate pendulum and arm velocities.
    
    Args:
        phi_history: circular buffer of recent phi measurements
        phi_dot_filt: previous filtered pendulum velocity
        step_rate: current step rate (steps/s)
        dt: time delta (seconds)
        n_diff: finite difference window size
        alpha_ema: EMA smoothing coefficient
    
    Returns:
        (phi_dot_filt_new, theta_dot_est)
    """
    # Pendulum velocity via finite difference + EMA filter
    phi_dot_raw = (phi_history[0] - phi_history[n_diff]) / (n_diff * dt)
    phi_dot_filt_new = alpha_ema * phi_dot_raw + (1 - alpha_ema) * phi_dot_filt
    
    # Arm velocity from step rate
    theta_dot_est = step_rate * RAD_PER_STEP / dt
    
    return (phi_dot_filt_new, theta_dot_est)

# ─────────────────────────────────────────────
#  ARM CENTERING (SHARED BY ALL STRATEGIES)
# ─────────────────────────────────────────────
def centering_ramp(theta: float, theta_soft_rad: float, theta_hard_rad: float) -> float:
    """
    Returns centering gain multiplier.
    1× within soft limit, ramps 1→6× toward hard limit.
    
    Args:
        theta: arm angle (radians)
        theta_soft_rad: soft limit threshold
        theta_hard_rad: hard limit threshold
    
    Returns:
        gain multiplier (float)
    """
    abs_theta = abs(theta)
    if abs_theta <= theta_soft_rad:
        return 1.0
    elif abs_theta <= theta_hard_rad:
        frac = (abs_theta - theta_soft_rad) / (theta_hard_rad - theta_soft_rad)
        return 1.0 + 5.0 * frac
    else:
        return 0.0   # past hard limit

def compute_centering_term(theta: float, ramp: float, k_center: float) -> float:
    """
    Compute arm centering contribution to control signal.
    
    Args:
        theta: arm angle (radians)
        ramp: centering ramp multiplier (from centering_ramp)
        k_center: centering gain constant
    
    Returns:
        arm acceleration command component (rad/s²)
    """
    return -k_center * ramp * theta

# ─────────────────────────────────────────────
#  CALIBRATION
# ─────────────────────────────────────────────
def calibrate_zero_interactive() -> int:
    """
    Calibrate ZERO_RAW by reading multiple samples with pendulum upright.
    Uses circular mean (atan2) for robustness.
    
    Returns:
        calibrated ZERO_RAW value
    """
    print("Hold the pendulum exactly upright, then press Enter to calibrate zero.")
    try:
        _ = input("Ready? ")
    except Exception:
        print("(No stdin available — using fallback.)")
        return 1750
    
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
    zero_raw = int(round(mean_ang * 4096 / (2 * math.pi))) % 4096
    print(f"Calibrated ZERO_RAW = {zero_raw}")
    
    return zero_raw

# ─────────────────────────────────────────────
#  STATE MACHINE CONSTANTS
# ─────────────────────────────────────────────
IDLE       = 0
ACTIVE     = 1
RECOVERING = 2
LIMIT_HIT  = 3
FAULT      = 4

STATE_NAMES = {0:"IDLE", 1:"ACTIVE", 2:"RECOVERING", 3:"LIMIT_HIT", 4:"FAULT"}
