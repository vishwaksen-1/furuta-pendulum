# Physics of the Furuta Pendulum

## 1. System Description

A Furuta pendulum has two degrees of freedom:

| Variable | Symbol | Description | Measured by |
|----------|--------|-------------|-------------|
| Arm angle | θ (theta) | Rotation of horizontal arm | Step count (open loop) |
| Pendulum angle | φ (phi) | Tilt of pendulum from vertical | AS5600 encoder |

The control objective is to keep **φ ≈ 0** (pendulum upright) by commanding arm angular acceleration **θ̈**.

### Coordinate System

```
        Z (up)
        |
        |   φ (pendulum angle from vertical)
        |  /
        | /  ← pendulum rod, length L
        |/
       [pivot]──── arm, length r ────[motor axis]
                                          │
                                       [motor]
```

- φ = 0 : pendulum perfectly upright
- φ > 0 : pendulum tilted in positive direction
- θ : arm angle (absolute value irrelevant; only θ̇ and θ̈ matter for control)

---

## 2. Equations of Motion

The full Euler-Lagrange equations of a Furuta pendulum are nonlinear and coupled. For balancing near the upright equilibrium (|φ| < ~15°), we apply **small-angle linearisation** (sin φ ≈ φ, cos φ ≈ 1):

### Linearised Equation of Pendulum Motion

$$\boxed{I_p \ddot{\phi} = m g \frac{L}{2} \phi - m \frac{L}{2} r \, \ddot{\theta}}$$

| Symbol | Meaning |
|--------|---------|
| m | pendulum mass [kg] |
| L | pendulum length [m] |
| r | arm length [m] |
| g | 9.81 m/s² |
| I_p | pendulum moment of inertia about pivot [kg·m²] |
| φ | pendulum angle from vertical [rad] |
| θ̈ | arm angular acceleration — **the control input** [rad/s²] |

### Pendulum Moment of Inertia

Treating the pendulum as a uniform thin rod rotating about one end:

$$I_p = \frac{1}{3} m L^2$$

---

## 3. State-Space Representation

Rearranging the linearised EOM:

$$\ddot{\phi} = \underbrace{\frac{mg(L/2)}{I_p}}_{\omega_n^2} \phi - \underbrace{\frac{m r (L/2)}{I_p}}_{B} \ddot{\theta}$$

$$\ddot{\phi} = \omega_n^2 \phi - B u \qquad \text{where } u = \ddot{\theta}$$

In state-space form with **x** = [φ, φ̇]ᵀ:

$$\dot{\mathbf{x}} = A\mathbf{x} + \mathbf{b}u$$

$$A = \begin{bmatrix} 0 & 1 \\ \omega_n^2 & 0 \end{bmatrix}, \qquad \mathbf{b} = \begin{bmatrix} 0 \\ -B \end{bmatrix}$$

The eigenvalues of A are **±ωₙ** — one stable pole (−ωₙ) and one **unstable pole** (+ωₙ). The positive eigenvalue is what makes this system non-trivial: without active control, any nonzero φ will grow exponentially.

---

## 4. Key System Parameters

### Natural Frequency (Unstable Pole)

$$\omega_n = \sqrt{\frac{3g}{2L}}$$

This is the rate at which the uncontrolled pendulum diverges. It sets the minimum speed requirement for the entire control system.

### Control Authority

$$B = \frac{3r}{2L}$$

B is the gain from arm acceleration to pendulum corrective acceleration. Higher arm length r → more authority. But larger r also increases the inertia the motor must accelerate — there is an optimal tradeoff.

### Instability Time Constant

$$\tau = \frac{1}{\omega_n}$$

The pendulum diverges with characteristic time τ. The control loop must complete a full sense-compute-actuate cycle in well under τ.

### Fall Time (Exact Solution)

For the inverted pendulum, the exact solution is φ(t) = φ₀ · cosh(ωₙ t). The time to fall from initial angle φ₀ to angle φ₁:

$$t_{fall} = \frac{1}{\omega_n} \cosh^{-1}\!\left(\frac{\phi_1}{\phi_0}\right)$$

---

## 5. Numerical Verification for Our System

**Our physical parameters:**

| Parameter | Symbol | Value |
|-----------|--------|-------|
| Pendulum mass | m | 0.030 kg |
| Pendulum length | L | 0.11 m |
| Arm length | r | 0.07 m |
| Arm + mount mass | m_arm | 0.060 kg |

### Step-by-step calculations

**Pendulum MOI:**
```
I_p = (1/3) × 0.030 × 0.11²
    = (1/3) × 0.030 × 0.0121
    = 1.21 × 10⁻⁴ kg·m²
```

**Natural frequency:**
```
ωₙ = √(3 × 9.81 / (2 × 0.11))
   = √(29.43 / 0.22)
   = √(133.8)
   = 11.57 rad/s  →  1.84 Hz
```

**Instability time constant:**
```
τ = 1 / 11.57 = 86.4 ms
```

**Fall time from 3° to 20°:**
```
t_fall = (1/11.57) × acosh(20/3)
       = 0.0864 × acosh(6.667)
       = 0.0864 × 2.587
       = 0.224 s  (224 ms)
```

**Control authority gain:**
```
B = 3 × 0.07 / (2 × 0.11)
  = 0.21 / 0.22
  = 0.955
```

### Motor Torque Budget

Total inertia seen by the motor:

```
I_arm_rod  = (1/3) × m_arm × r²  = (1/3) × 0.060 × 0.07²  = 9.8 × 10⁻⁵  kg·m²
I_pend_tip = m × r²               = 0.030 × 0.07²           = 1.47 × 10⁻⁴ kg·m²

I_total = 9.8e-5 + 1.47e-4 = 2.45 × 10⁻⁴ kg·m²
```

Available motor torque (17HS4401S at 70% current, low speed):
```
τ_motor ≈ 0.44 × 0.7 × 0.5  =  0.154 N·m   (hold × current% × running derating)
```

Maximum arm angular acceleration:
```
α_max = τ_motor / I_total = 0.154 / 2.45e-4 ≈ 629 rad/s²
```

Required arm acceleration to correct 5° tilt:
```
θ̈_needed = (ωₙ² / B) × φ
           = (133.8 / 0.955) × 0.0873
           = 140.1 × 0.0873
           = 12.2 rad/s²
```

**Authority ratio at 5°:** 629 / 12.2 ≈ **52×** — ample margin.

### Stepper Speed and Resolution

At 1/8 microstepping (1600 steps/rev), max reliable step rate 800 steps/s:

```
ω_arm_max = (800 / 1600) × 2π  =  3.14 rad/s  =  30 RPM
```

Step angular resolution:
```
δθ = 360° / 1600  =  0.225° per step  =  0.00393 rad
```

Equivalent pendulum correction per step:
```
δφ_equiv = B × δθ  =  0.955 × 0.00393  ≈  0.00375 rad  ≈  0.215°
```

This is the **quantisation limit** of the controller — the smallest correction the arm can apply.

### AS5600 Encoder Resolution

```
Resolution = 360° / 4096  =  0.0879° per count  =  0.00153 rad
```

The encoder resolves angle ~2.5× finer than the step quantisation limit. This is appropriate — the sensor is not the bottleneck.

### Summary Table

| Quantity | Value | Requirement | Status |
|----------|-------|-------------|--------|
| ωₙ | 11.57 rad/s (1.84 Hz) | < 5 Hz ideal | ✓ |
| τ instability | 86 ms | > 50 ms | ✓ |
| Fall time 3°→20° | 224 ms | > 100 ms | ✓ |
| α_max | 629 rad/s² | > 5× needed | ✓ (52×) |
| Step resolution | 0.225° | < 1.5° | ✓ |
| Encoder resolution | 0.088° | < step res | ✓ |
| Loop period (500 Hz) | 2 ms | < τ/10 = 8.6 ms | ✓ |

---

## 6. Validity of Linearisation

The linearised model is valid while sin φ ≈ φ, i.e. while |φ| is small. The approximation error is:

| φ | sin φ | φ (rad) | Error |
|---|-------|---------|-------|
| 5° | 0.0872 | 0.0873 | 0.1% |
| 10° | 0.1736 | 0.1745 | 0.5% |
| 15° | 0.2588 | 0.2618 | 1.2% |
| 20° | 0.3420 | 0.3491 | 2.1% |

The controller is derived assuming this model. Beyond ~15°, the nonlinear terms become non-negligible and the gain values are no longer theoretically justified. This is why the firmware disables the motor if |φ| > 15° — see [`03_constraints.md`](03_constraints.md).
