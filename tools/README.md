# Tools

## Feasibility Tracker

An interactive browser-based calculator that verifies your hardware parameters satisfy the physics and control bandwidth requirements **before you build anything**.

### How to Use

Open `feasibility_tracker.html` in any web browser. No server, no internet, no install needed.

**→ Just double-click the file.**

### What It Computes

All quantities are derived from first principles — the same equations in [`../docs/01_physics.md`](../docs/01_physics.md):

| Output | Derived from |
|--------|-------------|
| Natural frequency ωₙ | Pendulum length and mass |
| Instability time constant τ | ωₙ |
| Fall time (3° → 20°) | Exact inverted pendulum solution |
| Motor torque budget | Total arm inertia + available torque |
| Acceleration authority ratio | Motor α_max vs required α at 5° |
| Stepper torque-vs-speed curve | Simplified NEMA 17 model |
| Step resolution deadband | Microstepping + control authority B |
| Encoder velocity resolution | AS5600 12-bit resolution + loop rate |
| I²C timing budget | Byte count + clock rate |
| Cable wrap constraint | User-set arm rotation limit |

### Adjustable Parameters

| Parameter | What it affects |
|-----------|----------------|
| Pendulum mass | ωₙ, torque budget, authority ratio |
| Pendulum length | ωₙ (dominant), fall time |
| Arm length | Control authority B, inertia, centering |
| Arm + mount mass | Motor inertia load |
| Current limit % | Available motor torque |
| Microstepping | Step resolution, max arm speed |
| Max step rate | Arm bandwidth, torque operating point |
| Loop rate | Timing budget, velocity noise floor |
| I²C rate | Read latency budget |
| Max arm rotation | Cable wrap constraint check |

### Constraint Checklist

The tracker evaluates seven go/no-go checks and colour-codes each:

- ✓ Green — passes with margin
- ⚠ Amber — passes but tight; needs careful attention
- ✗ Red — fails; change a parameter

