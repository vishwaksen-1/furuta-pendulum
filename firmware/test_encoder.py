# test_encoder.py
# Test 2 of 6 — AS5600 angle read and zero calibration.
# Reads raw angle continuously. Use this to find your zero offset
# and check encoder noise at standstill.
#
# IMPORTANT: Note down the ZERO_RAW value printed here.
#            You will need it in main.py.

from machine import Pin, I2C
import time, math

i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400_000)
AS5600_ADDR = 0x36
REG_ANGLE_H = 0x0C   # high byte of 12-bit raw angle
REG_STATUS  = 0x0B   # bit 5 = MH (too strong), bit 4 = ML (too weak),
                     # bit 3 = MD (magnet detected — must be 1)

def read_raw_angle():
    data = i2c.readfrom_mem(AS5600_ADDR, REG_ANGLE_H, 2)
    return ((data[0] & 0x0F) << 8) | data[1]   # 12-bit, 0–4095

def read_status():
    return i2c.readfrom_mem(AS5600_ADDR, REG_STATUS, 1)[0]

# --- Magnet check ---
status = read_status()
print("=== AS5600 Magnet Status ===")
if status & 0x08:
    print("  Magnet detected (MD=1) — OK")
else:
    print("  ERROR: No magnet detected (MD=0)")
    print("  Check magnet position and gap (<3 mm).")
if status & 0x10:
    print("  WARNING: Magnet too weak (ML=1) — move magnet closer")
if status & 0x20:
    print("  WARNING: Magnet too strong (MH=1) — increase gap slightly")
print()

# --- Set zero ---
input("Hold pendulum EXACTLY upright. Press ENTER to record zero...")
zero_raw = read_raw_angle()
print(f"\n  >>> ZERO_RAW = {zero_raw} <<<")
print(f"  Copy this value into main.py as ZERO_RAW.\n")

COUNTS_PER_REV = 4096
DEG_PER_COUNT  = 360.0 / COUNTS_PER_REV
RAD_PER_COUNT  = 2 * math.pi / COUNTS_PER_REV

print("Reading angle (Ctrl+C to stop).")
print("Rotate pendulum slowly — values must change smoothly, no jumps.")
print("Noise at standstill should be ≤ ±2 counts (≤ ±0.18°).\n")

while True:
    raw = read_raw_angle()
    delta = raw - zero_raw
    if delta >  2048: delta -= 4096
    if delta < -2048: delta += 4096

    angle_deg = delta * DEG_PER_COUNT
    angle_rad = delta * RAD_PER_COUNT

    print(f"  raw={raw:4d}  φ={angle_deg:+7.2f}°  φ={angle_rad:+6.4f} rad")
    time.sleep_ms(50)
