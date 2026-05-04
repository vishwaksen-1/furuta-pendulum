# test_velocity.py
# Test 4 of 6 — Velocity estimation quality check.
# Hold pendulum still: phi_dot noise should be < ±30 °/s.
# Then tap pendulum and watch the filtered velocity respond.
#
# Tune ALPHA_EMA until noise at standstill is < ±20 °/s.
# Note the alpha value — use it in main.py.

from machine import Pin, I2C
import time, math

i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400_000)
AS5600_ADDR = 0x36

def read_raw_angle() -> int:
    data = i2c.readfrom_mem(AS5600_ADDR, 0x0C, 2)
    return ((data[0] & 0x0F) << 8) | data[1]

# ── Calibrate ZERO_RAW interactively ─────────────────────────────
print("=== Velocity Estimation Test ===")
print("Hold the pendulum exactly upright, then press Enter to calibrate zero.")
input("Ready? ")

samples = 25
sum_sin = 0.0
sum_cos = 0.0
for _ in range(samples):
    raw = read_raw_angle()
    ang = raw * (2 * math.pi / 4096)
    sum_sin += math.sin(ang)
    sum_cos += math.cos(ang)
    time.sleep_ms(5)

mean_ang = math.atan2(sum_sin, sum_cos)
if mean_ang < 0:
    mean_ang += 2 * math.pi
ZERO_RAW = int(round(mean_ang * 4096 / (2 * math.pi))) % 4096
print(f"Zero set to raw = {ZERO_RAW}\n")

RAD_PER_COUNT = 2 * math.pi / 4096
DT_MS  = 2            # 500 Hz loop
DT_S   = DT_MS / 1000.0

# Tunable parameters
ALPHA_EMA = 0.8      # EMA filter coefficient — lower = more smoothing, more lag
N_DIFF    = 3         # finite difference window (samples)

def read_angle_rad():
    raw = read_raw_angle()
    delta = raw - ZERO_RAW
    if delta >  2048: delta -= 4096
    if delta < -2048: delta += 4096
    return delta * RAD_PER_COUNT

phi_history      = [read_angle_rad()] * (N_DIFF + 2)
phi_dot_filtered = 0.0

print(f"  ALPHA_EMA = {ALPHA_EMA},  N_DIFF = {N_DIFF}")
print("  Hold pendulum still. phi_dot noise should be < ±30 °/s.")
print("  Tap pendulum and watch filtered velocity respond.")
print("  Ctrl+C to stop.\n")

while True:
    t0 = time.ticks_us()

    phi_history = [read_angle_rad()] + phi_history[:-1]

    # N-point finite difference
    phi_dot_raw = (phi_history[0] - phi_history[N_DIFF]) / (N_DIFF * DT_S)

    # EMA filter
    phi_dot_filtered = ALPHA_EMA * phi_dot_raw + (1 - ALPHA_EMA) * phi_dot_filtered

    phi_deg       = math.degrees(phi_history[0])
    raw_dps       = math.degrees(phi_dot_raw)
    filtered_dps  = math.degrees(phi_dot_filtered)

    print(f"  φ={phi_deg:+6.2f}°  φ̇_raw={raw_dps:+7.1f}°/s  φ̇_filt={filtered_dps:+7.1f}°/s")

    elapsed = time.ticks_diff(time.ticks_us(), t0)
    time.sleep_us(max(0, DT_MS * 1000 - elapsed))
