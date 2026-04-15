import math
import matplotlib.pyplot as plt

# Physics and Time
DT = 0.002           # 500 Hz
T_MAX = 3.0          # Simulate 3 seconds
STEPS = int(T_MAX / DT)
G = 9.81
L = 0.07             # 7cm arm length (from test_motor_encoder.py)

# Controller Gains (from your successful run)
KP = 190.0
KD = 42.0
K1 = 0.03            # Estimated k1

def simulate(mode: str):
    """Simulate pendulum response.

    Modes:
      - 'standard': u = KP*phi + KD*phi_dot
      - 'log_p':    u = (KP*phi)*log(|phi|/K1 + 1) + KD*phi_dot
      - 'log_pd':   u = (KP*phi + KD*phi_dot)*log(|phi|/K1 + 1)
    """
    phi = math.radians(15.0)  # Start dropped at 15 degrees
    phi_dot = 0.0

    time_log = []
    phi_log = []

    for i in range(STEPS):
        time_log.append(i * DT)
        phi_log.append(math.degrees(phi))

        # 1. Controller Math
        u_p = KP * phi
        u_d = KD * phi_dot

        if mode == "standard":
            u = u_p + u_d
        else:
            modifier = math.log((abs(phi) / K1) + 1.0)
            if mode == "log_p":
                u = (u_p * modifier) + u_d
            elif mode == "log_pd":
                u = (u_p + u_d) * modifier
            else:
                raise ValueError(f"Unknown mode: {mode}")

        u = max(-600, min(600, u))  # Clamp to ALPHA_MAX

        # 2. Physics (phi_ddot = (g/L)*sin(phi) - u)
        # Assuming the arm acceleration translates directly to pendulum base acceleration
        phi_ddot = (G / L) * math.sin(phi) - u

        # 3. Integration
        phi_dot += phi_ddot * DT
        phi += phi_dot * DT

    return time_log, phi_log

# Run simulations
t, phi_standard = simulate("standard")
_, phi_log_p = simulate("log_p")
_, phi_log_pd = simulate("log_pd")

# Plot Results (two horizontally stacked subplots)
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5), sharey=True)

ax1.plot(t, phi_standard, label="Standard PD", linewidth=2)
ax1.plot(t, phi_log_p, label=f"Log (k1={K1})", linewidth=2, linestyle="--")
ax1.axhline(0, color="black", linewidth=1)
ax1.set_title("non-linearity in p")
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("Pendulum Angle (degrees)")
ax1.grid(True)
ax1.legend()

ax2.plot(t, phi_standard, label="Standard PD", linewidth=2)
ax2.plot(t, phi_log_pd, label=f"Log (k1={K1})", linewidth=2, linestyle="--")
ax2.axhline(0, color="black", linewidth=1)
ax2.set_title("full non-linearity")
ax2.set_xlabel("Time (s)")
ax2.grid(True)
ax2.legend()

plt.tight_layout()
plt.show()
