# Gain Tuning Guide

Run all firmware tests in `firmware/` before starting this procedure. Do not attempt tuning without first verifying every subsystem independently.

---

## Starting Gains

Open `firmware/main.py` and set:

```python
KP = 940.0
KD = 42.0
K_CENTER = 1.5
ALPHA_EMA = 0.20
```

These correspond to ωc = 2.5 × ωₙ — conservative, slow, but safe to start.

---

## Round 1 — Verify Direction

Power up with pendulum held upright. Watch the serial output. Release the pendulum with **zero initial disturbance** (as straight up as you can hold it).

**The motor should immediately respond in the correct direction.** If the arm consistently drives the pendulum *away* from vertical (making it fall faster), you have a sign error. Fix by either:

- Negating `phi` in `read_phi()` — swap the sign convention, or
- Swapping `DIR_PIN` HIGH/LOW logic in `fire_steps()`

Do not proceed until the direction is correct.

---

## Round 2 — Find the Proportional Boundary

With correct direction confirmed, increase Kp in steps of 200:

```
940 → 1140 → 1340 → 1540 → 1758 → ...
```

After each increase, hold the pendulum up, release, and observe. You are looking for the transition from:

- **Too low Kp:** pendulum drifts slowly to one side and falls. Motor responds but not fast enough.
- **About right:** pendulum resists small disturbances and recovers.
- **Too high Kp:** arm oscillates rapidly left-right at high frequency (the motor buzzes). Back off 20%.

Note the Kp where oscillation begins. Your operating Kp should be **80% of that value**.

---

## Round 3 — Add Derivative Damping

With Kp set, increase Kd from 42 upward in steps of 5:

```
42 → 47 → 52 → 57 → 62 → ...
```

Signs of too-low Kd:
- Pendulum rocks back and forth multiple times before settling (underdamped)
- Sustained oscillation that does not decay

Signs of too-high Kd (or noisy velocity estimate):
- High-frequency arm chatter audible as buzzing, even when pendulum is nearly vertical
- Motor makes grinding noise in rapid direction alternation

If you get chatter before reaching good damping, reduce `ALPHA_EMA` to 0.10–0.15 (more smoothing on velocity) and try again. Alternatively, increase `N_DIFF` to 4 or 5.

---

## Round 4 — Test Disturbance Rejection

With Kp and Kd set, apply a deliberate tap to the pendulum (~5° disturbance). It should:

- Respond within one or two control cycles (4–8 ms)
- Correct back to vertical within ~0.5 s
- Not overshoot more than ~2–3° in the opposite direction

If recovery is sluggish, increase Kp by 10% and repeat. If overshoot is excessive, increase Kd by 5 and repeat.

---

## Round 5 — Arm Centering

Deliberately push the arm to ~30° from centre while the pendulum is being balanced. Release. The arm should:

- Slowly drift back toward centre over several seconds
- Not cause the pendulum to fall during centering

If balance breaks during arm centering, reduce K_CENTER (try 0.8–1.0). If the arm barely returns, increase K_CENTER toward 2.5.

---

## Round 6 — Nominal Gains

Once the conservative gains work well, try the nominal set:

```python
KP = 1858.0
KD = 59.4
```

This corresponds to ωc = 3.5 × ωₙ. Repeat Rounds 2–5 with these values. The response will be crisper and disturbance rejection faster. Adjust from these values based on what you observe.

---

## Interpreting Serial Output

```
[ACTIVE    ] φ=+0.34°  φ̇=  -2.1°/s  θ=+12.3°  step_rate=  +87  u=  -412
```

| Field | Meaning | Good value at balance |
|-------|---------|----------------------|
| φ | pendulum angle | < ±2° |
| φ̇ | pendulum velocity | < ±20 °/s |
| θ | arm angle | drifting slowly, < ±40° |
| step_rate | current arm speed | low magnitude during balance |
| u | control command (rad/s²) | fluctuating, not saturating |

If `u` is constantly at ±600 (the clamp), the gains are too high or the pendulum is too far from vertical. If `u` is near zero while the pendulum is visibly tilted, the gains are too low.

---

## Final Parameters (Fill In After Successful Run)

```python
# Record your tuned values here
KP         = ___
KD         = ___
K_CENTER   = ___
ALPHA_EMA  = ___
N_DIFF     = ___
ZERO_RAW   = ___   # from test_encoder.py
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Motor doesn't move at all | ENABLE pin not driven LOW | Check GP4 is pulled LOW in code |
| Motor moves but pendulum falls instantly | Direction wrong | Negate phi or swap DIR logic |
| Loud buzzing, arm vibrating | Kd too high or velocity too noisy | Reduce Kd, lower ALPHA_EMA |
| Pendulum drifts slowly | Kp too low | Increase Kp by 200 |
| Arm hits limit repeatedly | K_center too low | Increase K_center |
| Arm hits limit and balance breaks | K_center too high fighting PD | Reduce K_center |
| AS5600 reads jump erratically | Magnet not centred or gap too large | Adjust magnet position |
| Step count drifts, arm position wrong | Step loss at high speed | Reduce MAX_STEP_RATE to 600 |
