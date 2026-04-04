# Control Design

## 1. Why PD and Not PID

A natural first instinct is to use a PID controller. For an inverted pendulum, the **integral term is actively harmful**:

- The integrator accumulates error over time. During correction, it winds up, causes overshoot, winds up in the opposite direction, and triggers divergence — called **integrator windup**.
- On a system with an unstable pole, windup does not merely cause oscillation. It causes the system to fall.
- Additionally, an integrator will slowly walk the arm toward the cable wrap limit even during successful balancing, because any sustained small steady-state error produces a growing integral.

**We use PD control** — proportional on pendulum angle, derivative on pendulum angular velocity.

---

## 2. The Plant (What We Are Controlling)

From the linearised physics (see [`01_physics.md`](01_physics.md)):

$$\ddot{\phi} = \omega_n^2 \phi - B u, \qquad u = \ddot{\theta}$$

This is a second-order unstable system. In transfer function form (Laplace domain):

$$\frac{\Phi(s)}{U(s)} = \frac{-B}{s^2 - \omega_n^2}$$

The poles of the open-loop plant are at **s = ±ωₙ**. The positive pole at s = +ωₙ is the instability we must stabilise.

---

## 3. PD as Pole Placement

The PD control law:

$$u = -K_p \phi - K_d \dot{\phi}$$

Substituting into the plant equation:

$$\ddot{\phi} = \omega_n^2 \phi - B(-K_p \phi - K_d \dot{\phi})$$

$$\ddot{\phi} + B K_d \dot{\phi} + (B K_p - \omega_n^2)\phi = 0$$

This is a standard second-order ODE. Comparing to the canonical form:

$$\ddot{\phi} + 2\zeta\omega_c \dot{\phi} + \omega_c^2 \phi = 0$$

We identify:

$$\omega_c^2 = B K_p - \omega_n^2 \qquad \Longrightarrow \qquad \boxed{K_p = \frac{\omega_c^2 + \omega_n^2}{B}}$$

$$2\zeta\omega_c = B K_d \qquad \Longrightarrow \qquad \boxed{K_d = \frac{2\zeta\omega_c}{B}}$$

Where:
- ωc = desired closed-loop natural frequency [rad/s]
- ζ = desired damping ratio (dimensionless)

This is **pole placement**: we choose ωc and ζ, and the gains follow directly from the physics. No guessing.

---

## 4. Choosing Closed-Loop Poles

### Requirement 1: ωc > ωₙ

The closed-loop poles must be in the left half-plane. From the gain formula, this requires B·Kp > ωₙ², i.e. ωc > 0, which is always true by construction once we choose ωc > 0. In practice, ωc should be **several times** ωₙ for adequate disturbance rejection speed.

### Requirement 2: ζ ≈ 0.7

A damping ratio of 0.7 gives near-critically-damped response — fast settling with minimal overshoot. This is the standard design choice for servo systems and regulators.

### Requirement 3: ωc bounded by actuator limits

At angle φ, the control command is:

$$u = K_p \phi + K_d \dot{\phi}$$

The stepper can deliver at most α_max ≈ 629 rad/s². For a step disturbance of φ₀ = 5°, the peak command is approximately Kp × φ₀. So:

$$K_p \leq \frac{\alpha_{max}}{\phi_0} = \frac{629}{0.0873} \approx 7200$$

This gives enormous headroom. The practical upper bound on ωc is set by **velocity estimate noise**, not actuator limits.

### Design Point Selection

| Level | ωc | ωc / ωₙ | Character |
|-------|----|---------|-----------|
| Conservative | 2.5 × 11.57 = 28.9 rad/s | 2.5× | Start here — slow but safe |
| **Nominal** | **3.5 × 11.57 = 40.5 rad/s** | **3.5×** | **Recommended operating point** |
| Aggressive | 5.0 × 11.57 = 57.8 rad/s | 5.0× | Fast correction, sensitive to noise |

---

## 5. Gain Calculations

Using ζ = 0.7, B = 0.955, ωₙ = 11.57 rad/s:

### Conservative (ωc = 28.9 rad/s)

```
Kp = (28.9² + 11.57²) / 0.955
   = (835.2 + 133.9) / 0.955
   = 969.1 / 0.955
   ≈ 1015

Kd = 2 × 0.7 × 28.9 / 0.955
   = 40.46 / 0.955
   ≈ 42.4
```

### Nominal (ωc = 40.5 rad/s)

```
Kp = (40.5² + 11.57²) / 0.955
   = (1640.25 + 133.87) / 0.955
   = 1774.12 / 0.955
   ≈ 1858

Kd = 2 × 0.7 × 40.5 / 0.955
   = 56.7 / 0.955
   ≈ 59.4
```

### Aggressive (ωc = 57.8 rad/s)

```
Kp = (57.8² + 11.57²) / 0.955
   = (3340.84 + 133.87) / 0.955
   = 3474.71 / 0.955
   ≈ 3638

Kd = 2 × 0.7 × 57.8 / 0.955
   = 80.92 / 0.955
   ≈ 84.7
```

---

## 6. Velocity Estimation

The derivative term Kd·φ̇ requires angular velocity, but the AS5600 provides position. We differentiate numerically.

### Naive finite difference

$$\dot{\phi}[n] = \frac{\phi[n] - \phi[n-1]}{\Delta t}$$

At 500 Hz (Δt = 2 ms) and 12-bit resolution (0.088°/count), encoder noise of ±1 count produces:

```
φ̇ noise = ±0.088° / 0.002 s = ±44 °/s = ±0.77 rad/s
```

Multiplied by Kd = 59.4: **±45 rad/s² injected noise** in the control signal. This is ~7% of α_max — significant but manageable.

### N-point finite difference

Using a wider window reduces noise:

$$\dot{\phi}[n] = \frac{\phi[n] - \phi[n-N]}{N \cdot \Delta t}$$

With N = 3, noise reduces by factor √3 ≈ 1.73, at the cost of N·Δt = 6 ms additional lag.

### Exponential Moving Average (EMA)

Applied to the derivative estimate:

$$\dot{\phi}_{filtered}[n] = \alpha \cdot \dot{\phi}_{raw}[n] + (1 - \alpha) \cdot \dot{\phi}_{filtered}[n-1]$$

α = 0.2 gives good noise rejection. The effective lag introduced is approximately (1-α)/α × Δt ≈ 8 ms. Given our fall time of 224 ms, this is acceptable.

**In firmware:** we combine both — N=3 finite difference followed by EMA with α=0.2.

---

## 7. Arm Centering

The arm has no position feedback and cannot rotate freely (cable wrap). Without centering, the PD controller will drift the arm to a limit during sustained corrective action.

We add a soft centering term:

$$u_{center} = -K_{center} \cdot \theta_{arm} \cdot f_{ramp}(\theta_{arm})$$

Where f_ramp smoothly increases the centering authority as the arm approaches the hard limit:

```
f_ramp(θ) = 1.0                                         if |θ| ≤ θ_soft
           = 1 + 5×(|θ| - θ_soft)/(θ_hard - θ_soft)   if θ_soft < |θ| ≤ θ_hard
```

K_center = 1.5 rad/s² per rad of arm displacement. This is small enough to not fight the PD term during normal operation.

---

## 8. Complete Control Law

$$u_{pd} = -K_p \phi - K_d \dot{\phi}_{filtered}$$

$$u_{center} = -K_{center} \cdot \theta \cdot f_{ramp}(\theta)$$

$$u = \text{clamp}(u_{pd} + u_{center},\ -\alpha_{max},\ +\alpha_{max})$$

The arm step rate is then integrated from u:

$$\dot{\theta}_{cmd}[n] = \dot{\theta}_{cmd}[n-1] + u \cdot \Delta t$$

This is converted to steps/second and sent to the A4988 through a trapezoidal rate limiter (see firmware).

---

## 9. Control Signal Flow

```
AS5600 ──I²C──► read φ_raw
                    │
                    ▼
              subtract zero offset
                    │
                    ▼
              N-point finite diff ──► φ̇_raw
                    │                    │
                    │              EMA filter
                    │                    │
                    │                    ▼ φ̇_filtered
                    │
              ──────┴──────────────────────────┐
                                               │
         u_pd = −Kp·φ − Kd·φ̇_filtered        │
                                               │
         θ_arm = step_count × rad/step         │
         u_center = −K_center·θ·f_ramp(θ)     │
                                               │
         u = clamp(u_pd + u_center, ±α_max)   │
                                               │
         target_step_rate += u × Δt × (N/2π)  │
                                               │
         rate_limiter (trapezoidal ramp)        │
                                               │
         fire step pulses ──► A4988 ──► motor  │
```

---

## 10. State Machine

The controller is embedded in a state machine to handle edge cases safely:

```
   ┌─────────────────────────────────────────────────────┐
   │                                                     │
   │   IDLE ──(|φ|<5° for 500ms)──► ACTIVE               │
   │                                    │                │
   │                         (|φ|>15°)  │  (|θ|>60°)     │
   │                              ▼     │      ▼         │
   │                         RECOVERING │  LIMIT_HIT     │
   │                              │     │      │         │
   │                 (|φ|<5° 500ms)     │  (|θ|<50°,     │
   │                              └─────┘   |φ|<5° 500ms)│
   │                                        └───► ACTIVE │
   │                                                     │
   │   Any state ──(I²C error)──► FAULT                  │
   └─────────────────────────────────────────────────────┘
```

| State | Motor | Description |
|-------|-------|-------------|
| IDLE | Off | Waiting for pendulum to be held upright |
| ACTIVE | On | PD control running |
| RECOVERING | Off | Pendulum fell past 15°; wait for manual reset |
| LIMIT_HIT | Off | Arm hit cable wrap limit |
| FAULT | Off | Sensor error |
