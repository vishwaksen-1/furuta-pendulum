# STL Files — 3D Printed Parts

Mechanical components designed and printed for this project.

> *Special thanks to our friend Akshit Kumar from the Mechanical Engineering Department for designing these parts and spending his time and effort to get the geometry right for our specific hardware constraints.*

---

## Parts List

| File | Description | Material | Infill |
|------|-------------|----------|--------|
| `base_mount.stl` | Motor shaft plate with pendulum and sensor mounts | PLA | 100% |
| `pendulum.stl` | Horizontal rotating arm(7 cm) and pendulum (11 cm) | PLA | 50% |



## Assembly Notes

- The arm attaches to the NEMA 17 motor shaft directly via D-shaft coupling. Make sure there is a tight fit, if not apply a drop of CA glue. Any slip corrupts the control loop and can cause instability.
- Pendulum arm attaches to the ring on the base mount with a (5mm x 10 mm x 5mm) bearing. The fit should be snug but not too tight to cause binding. Apply a drop of CA glue if loose.
- And the same end of the pendulum arm has a magnet cap that faces the AS5600 encoder chip on the base mount. The magnet should be centered and parallel to the chip for best results.
- The encoder mount positions the AS5600 chip at **1–2 mm** from the magnet face. Verify the MD bit reads 1 after assembly (see `firmware/test_encoder.py`).
- The encoder mound must be screwed down firmly to the base mount to prevent any wobble. Any movement of the encoder relative to the magnet will cause noisy readings and instability.