# LQR Control Design for Furuta Pendulum

**Status**: ⚠️ **NOT YET TESTED** — This is a new implementation pending hardware validation.

## Overview

The Linear Quadratic Regulator (LQR) is an optimal control strategy that uses full state-feedback to minimize a cost function. Unlike the traditional PD controller in `main-lin.py`, the LQR controller in `main-lqr.py` uses information from all four system states simultaneously to compute the arm acceleration command.

## State Representation

The full system state is represented as a 4-dimensional vector:

$$\mathbf{x} = \begin{bmatrix} \phi \\ \dot{\phi} \\ \theta \\ \dot{\theta} \end{bmatrix}$$

Where:
- **φ** = Pendulum angle from vertical [rad] (0 = upright)
- **φ̇** = Pendulum angular velocity [rad/s]
- **θ** = Arm angle [rad] (absolute position from activation zero)
- **θ̇** = Arm angular velocity [rad/s]

## Control Law

The LQR control computes the arm angular acceleration as:

$$u = u_{\text{LQR}} + u_{\text{center}}$$

### LQR Term

$$u_{\text{LQR}} = -\mathbf{K} \cdot \mathbf{x} = -[k_1, k_2, k_3, k_4] \cdot [\phi, \dot{\phi}, \theta, \dot{\theta}]^T$$

Where **K** is the optimal gain matrix determined by solving the LQR problem.

### Centering Term

$$u_{\text{center}} = -K_{\text{center}} \cdot r(\theta) \cdot \theta$$

This term is **identical to the PD controller**:
- Uses the same **virtual spring** to bring the arm back toward center
- Uses the same **centering ramp** `r(θ)` that increases gain as arm approaches hard limits
- Provides arm centering independent of pendulum stabilization

## Gain Sets

Three tuned gain sets are provided in `main-lqr.py`. Each assumes different cost weights on the four state variables.

### Conservative (Default)
```python
K_LQR = [150.0, 42.0, 6.0, 2.0]
```
**Derivation**: `Q = diag(100, 10, 10, 1)`, `R = 0.1`
- Emphasizes pendulum angle φ over arm position
- Lower control effort
- **Use this to start testing**

### Nominal
```python
K_LQR = [200.0, 50.0, 10.0, 3.0]
```
**Derivation**: `Q = diag(150, 20, 15, 2)`, `R = 0.1`
- Balanced weighting across states
- Moderate control effort
- **Use if conservative is too sluggish**

### Aggressive
```python
K_LQR = [250.0, 60.0, 15.0, 4.0]
```
**Derivation**: `Q = diag(200, 30, 20, 3)`, `R = 0.05`
- Higher control effort with larger gains
- **Use only if nominal is insufficient**

## Gain Interpretation

| Gain | Affects | Meaning |
|------|---------|---------|
| k₁ (≈150) | **φ** | Strong pendulum angle feedback — core balancing |
| k₂ (≈42) | **φ̇** | Damping on pendulum velocity — prevents overshoot |
| k₃ (≈6) | **θ** | Arm position feedback — helps centering |
| k₄ (≈2) | **θ̇** | Damping on arm velocity — smooth motion |

## Comparison with PD Control

| Aspect | PD (`main-lin.py`) | LQR (`main-lqr.py`) |
|--------|-------------------|-------------------|
| **Feedback** | 2 states: φ, φ̇ | 4 states: φ, φ̇, θ, θ̇ |
| **Optimality** | Hand-tuned poles | Optimal (minimizes cost) |
| **Arm centering** | Separate K_center gain | Integrated in K₃, K₄ + K_center |
| **Control effort** | Fixed gains KP, KD | All states weighted in LQR |
| **Tuning** | Frequency response | Cost function weights Q, R |

## Implementation Notes

### Arm Velocity Estimation

Since the arm has no velocity sensor, θ̇ is estimated from the step rate:

$$\dot{\theta} = \frac{\text{step\_rate} \times \text{RAD\_PER\_STEP}}{DT_S}$$

This estimate is **noisy** but adequate since the step rate is already smoothed by the motor acceleration limiter.

### Saturation

All control commands are saturated to `[-ALPHA_MAX, +ALPHA_MAX]` (±600 rad/s²) before being converted to motor commands.

### Centering Ramp Still Active

The arm centering ramp is **unchanged from the PD controller**:
- Ramps from 1× to 6× gain as arm approaches hard limit
- Prevents excessive motor excursions
- Works in conjunction with K₃, K₄ LQR terms

## Testing Procedure

1. **Load `main-lqr.py` on the Pico**
2. **Calibrate ZERO_RAW** (same as PD controller)
3. **Verify the conservative K_LQR gains activate**
4. **Hold pendulum upright and release** — observe balance behavior
5. **If unstable**: Check K_LQR signs and magnitudes
6. **If too sluggish**: Advance to Nominal gains
7. **If aggressive overshoot**: Step back to Conservative gains

## Cost Function

The underlying LQR cost function minimizes:

$$J = \int_0^{\infty} \left( \mathbf{x}^T Q \mathbf{x} + u^2 R \right) dt$$

Where:
- **Q** = State weighting matrix (diagonal for simplicity)
- **R** = Control effort weighting (scalar)
- Larger Q elements penalize deviations in that state
- Larger R penalizes control effort (smoother but slower response)

## File Reference

- **Implementation**: `/firmware/main-lqr.py`
- **PD Reference**: `/firmware/main-lin.py` (keep for comparison)
- **Hardware setup**: See `04_hardware_setup.md`
- **Constraints**: See `03_constraints.md`

## Future Work

- [ ] Validate on hardware with conservative gains
- [ ] Compare transient response vs. PD controller
- [ ] Optimize gain sets based on measured plant dynamics
- [ ] Add adaptive gain scheduling if needed
- [ ] Consider LQR with integral action for zero steady-state error

### IF SUCCESSFUL: CONSIDER CHECKING OUT THE BRANCH `lqr-dev` and CONTRIBUTING BACK TO MAINLINE!

---

**Last Updated**: May 4, 2026  
**Status**: Pending hardware testing  
**Contact**: EECE Design Lab, IIT Kharagpur
