# System Constraints

## Hard Constraints

These cannot be violated. The firmware enforces them unconditionally.

---

### C1. Arm Rotation Limit (Cable Wrap)

**Limit: ±60° from centre.**

The AS5600 encoder wires run from the pendulum pivot along the arm to the fixed base. Unrestricted arm rotation will yank these wires out.

**Enforcement:**

```
Software soft limit : ±50°  — centering gain ramps up 1× → 6×
Software hard stop  : ±60°  — motor disabled, state → LIMIT_HIT
Physical hard stop  : recommend a mechanical peg at ±65° as backup
```

**Implication for control:** the arm is not a free actuator. During a large disturbance, the controller may exhaust its arm travel before fully correcting. In this case the pendulum will fall — this is correct behaviour. Cables take priority over the pendulum.

**Routing recommendation:** leave a service loop (small coil of slack) in the wire at the pivot. Do not route wires taut. A JST connector at the arm-base junction allows the arm to be removed without desoldering.

---

### C2. Stepper Torque-Speed — Silent Step Loss

The A4988 drives the stepper open-loop. If commanded acceleration exceeds what the motor can deliver at the current step rate, the rotor skips steps **silently** — no error is raised. The firmware's step count then diverges from the actual arm position.

**Consequence:** firmware thinks arm is at 30°; arm is actually at 55° and about to hit the physical stop.

**Mitigations:**
- Never exceed 800 steps/s at 1/8 microstepping (tested safe zone)
- Never change step rate by more than 4000 steps/s² per second (trapezoidal ramping)
- Use the motor characterisation test (`test_motor_encoder.py`) to empirically verify the stall threshold before running the main controller
- Monitor φ deflection during operation — unexpected large deflections at low commanded rates indicate step loss

---

### C3. Linearisation Valid Only Near Upright

The PD gains are derived from the linearised model, valid for |φ| < ~15°. Beyond this, nonlinear terms dominate and the theoretical gains are incorrect.

**Enforcement:** if |φ| > 15°, the firmware disables the motor and enters RECOVERING state. The controller does not attempt large-angle recovery.

---

## Soft Constraints

These limit performance but do not cause immediate failure.

---

### C4. I²C Timing Budget

| Operation | Time |
|-----------|------|
| AS5600 angle read (2 bytes at 400 kHz) | ~100–150 µs |
| Control computation | ~50 µs |
| Step pulse generation | ~10 µs (at 800 steps/s) |
| **Total per loop** | **~200 µs** |
| Loop period at 500 Hz | 2000 µs |
| **Timing margin** | **~1800 µs (90%)** |

There is ample headroom. If timing becomes tight (e.g. at higher loop rates), use a single repeated-start I²C transaction to read both AS5600 angle bytes rather than two separate reads.

---

### C5. Motor Thermal Dissipation

At 70% of rated current (0.7 A/phase) and 1.5 Ω phase resistance:

```
P ≈ I² × R = 0.7² × 1.5 ≈ 0.74 W per phase ≈ 1.5 W total
```

The motor will reach ~60–70°C during extended operation. The A4988 has thermal shutdown protection. For a lab demonstration session this is acceptable. Do not leave the system powered and stationary for extended periods.

---

### C6. Step Quantisation Dead Band

At 1/8 step, the minimum pendulum correction the controller can apply corresponds to:

```
δφ_min = B × δθ_step = 0.955 × 0.00393 rad ≈ 0.00375 rad ≈ 0.215°
```

Below this angle, the arm cannot produce a smaller correction — the next step either over-corrects or under-corrects. This creates a **limit cycle**: the pendulum oscillates within roughly ±0.2° at steady state. This is normal and expected for an open-loop stepper-driven system.

---

### C7. Velocity Estimate Noise Floor

With N=3 finite difference and α=0.2 EMA:
- Noise floor on φ̇: approximately ±25 °/s
- This injects Kd × 0.44 rad/s ≈ ±26 rad/s² of noise into u at nominal gains
- This is ~4% of α_max — acceptable but not negligible

If motor chatter is observed (arm buzzing at high frequency while pendulum is stable), reduce Kd by 10–15% or increase EMA smoothing (reduce α toward 0.10).

---

## Constraint Summary

| Constraint | Type | Limit | Firmware Response |
|---|---|---|---|
| Arm rotation | Hard | ±60° | Motor off → LIMIT_HIT |
| Arm soft limit | Soft | ±50° | Ramp centering gain |
| Pendulum angle | Hard | ±15° | Motor off → RECOVERING |
| Step rate | Hard | ≤ 800 steps/s | Rate-clamped in code |
| Step acceleration | Hard | ≤ 4000 steps/s² | Trapezoidal ramp enforced |
| Linearisation zone | Soft | |φ| < 15° | Already enforced by hard limit |
| Motor temperature | Soft | < 80°C | Reduce current if extended run |
