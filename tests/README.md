# Planned validation

Track geometry and headless preview tests are implemented in `test_track.py`.
`test_fastf1_import.py` checks SI conversion, raw-data hashes, and fallback to a
valid lap with a mocked data source; it never makes network requests.
Run `conda activate BiCS` followed by `python -m pytest -q` from the project root.
Add the remaining executable tests alongside each milestone; there is no simulator yet.

- `test_track.py`: closed geometry, invalid overlaps, ordered directional gates, nearest projection (continuity handling pending), raycasts, full-car boundary containment.
- `test_vehicle.py`: acceleration/braking, steering and yaw signs, grip limits, stability, timestep convergence.
- `test_powertrain.py`: force/power caps, delivered-power ERS accounting, energy bounds, no free regeneration.
- `test_environment.py`: 16 observations/3 actions, finite bounds, deterministic resets/trajectories, episode termination, headless operation.
- `test_evolution.py`: fixed vehicle across genomes, isolated evaluations, fitness resistance to shortcuts/oscillation, saved champion reconstruction.

## Test TODOs

- [ ] **M1.10 / M1.11** — Extend existing geometry/gate edge cases as recorded in [TODO.md](../TODO.md).
- [ ] **M2A.6 / M2B.6 / M2C.10 / M2D.5 / M2D.6** — Create configuration, physics, and energy tests with their implementations.
- [ ] **M3B.8 / M3B.9** — Create environment exploit, termination, state-isolation, and determinism tests.
- [ ] **M4A.6 / M4B.6 / M4C.9** — Create controller, fitness, and training-persistence tests.
- [ ] **M5A.9** — Create aggregation and benchmark comparability tests.
- [ ] **D8** — Record actual coverage after each milestone; distinguish directional gate tests from ordered episode completion tests.
