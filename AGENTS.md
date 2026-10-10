# Codex project instructions

Read `docs/PROJECT_SPEC.md` before implementing or changing project architecture.

- Project: Python BSP, evolutionary F1 racing agents with `neat-python`.
- NEAT evolves neural network weights and topology, **not** vehicle specifications. Keep the car and setup fixed during initial NEAT training.
- Start simple: offline FastF1-derived synthetic tracks, fixed F1-inspired car, headless simulator, 16-input/3-output controller.
- Separate track geometry, vehicle dynamics, powertrain, environment, NEAT training, rendering, and evaluation.
- Physics in SI units; fixed timesteps; deterministic seeds; validated, serializable vehicle configuration that can be passed into independent environment evaluations.
- Rendering must never be required for training. FastF1 must never be called in the training loop.
- Test geometry, checkpoints, vehicle footprint collision, dynamics, ERS energy accounting, and fitness against exploits.
- Mark modelling assumptions as assumptions; do not claim official FIA accuracy.
- Work milestone by milestone and keep code reviewable. Avoid introducing extra dependencies without a demonstrated need.

## Deferred extension — DEAP (do not implement now)

- DEAP may **later** optimize bounded car **setup** parameters (e.g., aero balance, downforce/drag trade-off, brake bias) while `neat-python` continues to evolve the driver.
- Preferred future workflow: train NEAT on a fixed car → freeze champion → optimize setup with DEAP → optionally retrain NEAT. Do not implement simultaneous co-evolution as part of the initial scope.
- Keep `VehicleConfig`, `RacingEnv`, and metrics independent of any optimizer so the future extension can reuse them.
- **Do not add DEAP to dependencies, create a setup optimizer, or start setup-evolution experiments unless explicitly requested at a later stage.**
