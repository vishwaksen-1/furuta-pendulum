# test_i2c_scan.py
# Test 1 of 6 — Run this first.
# Confirms AS5600 is wired correctly and responding on I2C.
# Expected output: device found at 0x36

from machine import Pin, I2C
import time

i2c = I2C(1, sda=Pin(14), scl=Pin(15), freq=400_000)

print("Scanning I2C bus...")
devices = i2c.scan()

if not devices:
    print("ERROR: No I2C devices found.")
    print("Check: VCC connected? SDA/SCL not swapped? Pull-ups present?")
else:
    for addr in devices:
        name = "AS5600" if addr == 0x36 else "unknown"
        print(f"  Found device at 0x{addr:02X} ({name})")
    if 0x36 in devices:
        print("\nAS5600 OK — proceed to test_encoder.py")
    else:
        print("\nWARNING: AS5600 (0x36) not found. Check wiring.")
