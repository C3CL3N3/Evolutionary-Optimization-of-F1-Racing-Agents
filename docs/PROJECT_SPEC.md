# Evolutionary Optimization of Formula 1 Racing Agents

**Project specification — draft v1.1**  
**Type:** Bachelor Semester Project (BSP)  
**Implementation language:** Python  
**Primary neuroevolution library:** [`neat-python`](https://neat-python.readthedocs.io/en/latest/)  
**Status:** Design specification; physical parameters and experimental settings are initial assumptions requiring validation.

## 1. Project overview

Develop a reproducible, lightweight, two-dimensional racing simulator in which autonomous agents learn to drive an F1-inspired car using neuroevolution. Each agent is a neural-network controller evolved with NEAT. The simulator supplies vehicle-state and track observations, applies the controller's steering/throttle/brake commands through a physically constrained car model, and measures lap progress, completion, safety, and lap time.

**Primary research question:** Can NEAT evolve controllers that reliably complete laps and subsequently improve lap times in a simplified Formula 1 racing environment?

**Potential extensions (deferred):** Cross-track transfer, learned ERS deployment, and **vehicle setup optimization with DEAP**. None is part of the initial implementation or required for the core research question.

### 1.1 Guiding principles

- Start with a simple, testable model and increase fidelity in stages, following the guidance from the meeting with Yiting Liu.
- Keep the neural controller compact; NEAT evolves connection weights **and**, if enabled in its configuration, network topology.
- Reuse established libraries rather than reinventing track geometry, evolutionary algorithms, plotting, or environment interfaces.
- Keep all vehicle specifications and setup parameters fixed across genomes during the main experiment; NEAT evolves the **driver**, not the car. Make vehicle parameters configurable so later setup optimization can reuse the same simulator.
- Run training headlessly and deterministically; visualization must be optional.
- Maintain strict separation between source data, track preprocessing, vehicle physics, controller, evolution, and evaluation.
- Use SI units internally: m, s, kg, N, W, J, rad.

## 2. Scope and deliverables

### 2.1 Minimum viable project

1. Import an F1-derived lap trajectory and construct a synthetic fixed-width road.
2. Implement track geometry, collision checking, lap progress, ordered checkpoints, and track sensors.
3. Implement and validate a driveable car, first with a kinematic bicycle model and then with a 3-DOF dynamic bicycle model.
4. Add friction-limited tyres, braking, aerodynamic drag/downforce, and simplified ICE + ERS propulsion.
5. Expose a consistent racing environment with reset/step methods and normalized observations.
6. Integrate `neat-python` to evolve autonomous controllers.
7. Compare learned agents against a simple non-learning baseline using repeatable metrics.
8. Save trained genomes, configurations, replay trajectories, and plots for the final report.

### 2.2 Out of scope initially

- Full FIA-accurate circuit boundaries, elevations, kerbs, pit lanes, and surface mapping.
- Suspension, wheel-by-wheel tyre dynamics, thermal tyre wear, detailed gearbox, fuel usage, and engine internals.
- Opponent vehicles, overtaking, drafting, multi-car collisions, race strategy, and race control.
- Evolving fundamental vehicle properties or car setup together with the NEAT network. **DEAP-based setup optimization is explicitly deferred to a later stage.**
- A fully regulation-compliant 2026 ERS/active-aero implementation.

## 3. System architecture

```text
Track source (FastF1 / synthetic)
          |
          v
Track preprocessing --> saved processed track
                                |
                                v
                         Racing environment <---- Vehicle model
                                |                 (tyres, aero, powertrain)
                         observations
                                |
                                v
                        NEAT controller
                                |
                         driving actions
                                |
                                v
                         Physics update
                                |
                      metrics + lap fitness
                                |
                                v
                         NEAT evolution

Renderer, baseline driver, and evaluator interact with the environment
but do not belong inside its physics implementation.
```

**Ownership:** A `RacingEnv` instance owns mutable episode state. The `Track` holds mostly immutable geometry. A `Vehicle` instance advances its own physical state. A controller maps observations to actions. The NEAT trainer evaluates genomes through independent environment resets.

## 4. Track generation and representation

### 4.1 Data source and accuracy

Use [FastF1](https://docs.fastf1.dev/) position data from a selected recorded lap as the **reference trajectory**. This is a driver's path, **not an official FIA centreline or surveyed track boundary**. `session.get_circuit_info()` supplies circuit annotation information such as corners; its standard API does not expose official `centers` or `edges` arrays. The resulting road must be described as a **synthetic constant-width track derived from lap telemetry**.

Select an available session with valid positional data (for example, a completed race from a prior season); do not assume a future or incomplete session has usable data. Record season, event, session, driver, lap identifier, and data provenance. Check coordinate units against the installed FastF1 version; FastF1 position coordinates are commonly expressed in decimetres and should be converted to metres where applicable.

### 4.2 Offline preprocessing pipeline

1. Load the session and select a suitable valid lap.
2. Extract ordered X/Y position samples, discard invalid/duplicate points, and detect discontinuities.
3. Convert to metres and align coordinates to a convenient local origin.
4. Smooth conservatively; preserve corner geometry, especially chicanes.
5. Resample by approximate arc length (initial target: 1–2 m between samples).
6. Close the loop without introducing a spurious segment across a large data gap; reject or repair incomplete laps.
7. Build a `LineString` and a road polygon using a constant-width buffer (initial width: **12 m total**, i.e. 6 m per side).
8. Validate geometry: nonempty, valid, reasonable circuit length, no unintended shortcuts or road self-overlaps, and continuous boundaries.
9. Build ordered checkpoint gates and a start/finish gate; calculate cumulative arc length, local tangents, and spatial lookup structures.
10. Save processed geometry and source metadata for reuse. Training must never call FastF1.

**Geometric caveat:** Buffering a line creates the union of all points within half the width. In tight turns or closely spaced parallel segments, this may merge distinct road sections. Detect these cases and reject or correct problematic tracks; a buffer alone is not a guarantee of valid racing topology.

### 4.3 Track object interface

| Method | Contract |
|---|---|
| `is_on_track(x, y)` | Is the point inside/on the road polygon? |
| `contains_car(pose, length, width)` | Is the **entire oriented rectangular footprint** inside the road? |
| `project(x, y, previous_progress=None)` | Reference-path projection with continuity handling |
| `get_progress(...)` | Ordered longitudinal progress in metres, with lap count handled separately |
| `get_lateral_offset(...)` | Signed lateral deviation from reference path |
| `get_heading_error(...)` | Wrapped angular difference to reference-path tangent |
| `get_lookahead(progress, distance)` | Reference direction or point at future arc length |
| `raycast(x, y, angle, max_range)` | Distance to nearest boundary along a sensor ray |
| `crossed_checkpoint(previous_pose, current_pose)` | Directional crossing of the next required checkpoint |

**Progress/fitness safety:** A nearest-point projection alone can jump to another segment or reward shortcuts. Track progress continuously and require checkpoints in order, with direction checks. Define completion only when all required gates are crossed and the finish line is crossed in the correct direction.

**Collision fidelity:** Centre-point containment is useful for debugging but insufficient for final evaluations. Use a rotated car rectangle (5.2 m × 1.9 m initially), optionally a cheaper approximation during early prototyping. Define whether contact with the boundary counts as a collision and use the same rule throughout.

## 5. Vehicle model

### 5.1 Baseline characteristics

All values below are **initial simulation assumptions or F1-inspired targets**, not a validated real 2026 F1 car specification.

| Parameter | Baseline | Units / notes |
|---|---:|---|
| Mass | 760 | kg |
| Body length | 5.20 | m, assumed |
| Body width | 1.90 | m |
| Wheelbase | 3.40 | m |
| CG to front axle, `lf` | 1.55 | m |
| CG to rear axle, `lr` | 1.85 | m; `lf + lr = wheelbase` |
| CG height | 0.30 | m, assumed |
| Yaw inertia | 1,150 | kg·m², assumed |
| Drivetrain | RWD | Rear-wheel drive |
| Longitudinal friction coefficient | 1.7 | assumed |
| Lateral friction coefficient | 1.8 | assumed |
| Front cornering stiffness | 90,000 | N/rad, assumed |
| Rear cornering stiffness | 100,000 | N/rad, assumed |
| Aerodynamic drag area, `CdA` | 1.0 | m², assumed |
| Aerodynamic downforce area, `ClA` | 4.5 | m², assumed |
| Air density | 1.225 | kg/m³ |
| Steering angle limit | ±0.35 | rad, assumed |
| Steering rate limit | 0.8 | rad/s, assumed |

The high-speed handling implied by the friction, cornering stiffness, and aero parameters must be calibrated and tested. Do not describe these as exact 2026 FIA values.

### 5.2 Dynamics

Use a **3-DOF planar dynamic bicycle model** with state

```python
VehicleState(
    x, y, heading,  # world-frame pose
    vx, vy,          # body-frame longitudinal and lateral velocity
    yaw_rate,
    steering_angle,
    ers_energy,
)
```

The model includes:

- Longitudinal acceleration and braking.
- Lateral velocity and yaw dynamics.
- Front and rear slip angles and lateral tyre forces.
- Combined longitudinal/lateral tyre-grip limits (friction circle/ellipse).
- Aerodynamic drag and downforce proportional to squared speed.
- Steering angle and steering rate constraints.
- Optional longitudinal load transfer in a later stage.

Representative equations, with a consistent body-frame sign convention:

\[
\dot{x}=v_x\cos\psi-v_y\sin\psi,\quad
\dot{y}=v_x\sin\psi+v_y\cos\psi,\quad
\dot{\psi}=r.
\]

\[
\dot{v}_x=\frac{F_{x,f}\cos\delta-F_{y,f}\sin\delta+F_{x,r}-F_{\mathrm{drag}}}{m}+rv_y.
\]

\[
\dot{v}_y=\frac{F_{y,f}\cos\delta+F_{x,f}\sin\delta+F_{y,r}}{m}-rv_x.
\]

\[
\dot r=\frac{l_f(F_{y,f}\cos\delta+F_{x,f}\sin\delta)-l_rF_{y,r}}{I_z}.
\]

The front and rear forces must be computed with one internally consistent slip-angle and force sign convention. Clamp tyre forces to axle friction limits, and avoid numerical singularities at low speed (e.g. a kinematic fallback/blending region). A fixed integration timestep is required; start with semi-implicit Euler and test stability before considering a higher-order integrator.

### 5.3 Propulsion and braking: simplified ICE + ERS

| Parameter | Baseline | Status |
|---|---:|---|
| ICE nominal maximum power | 400 kW | F1-inspired approximation |
| ERS maximum electrical power | 350 kW | Reference limit; actual availability constrained |
| Combined nominal power | 750 kW | Not continuously available |
| Drivetrain efficiency | 0.92 | Assumed |
| Usable ERS energy window | 4 MJ | Simplified energy budget, not full battery capacity |
| Low-speed drive-force cap | 12 kN | Assumed/calibrate |
| Maximum regen power | 150 kW | Initial implementation assumption |
| Maximum regen force | 4 kN | Initial implementation assumption |
| Regen efficiency | 0.70 | Assumed |
| Transmission | Implicit | No individual gear simulation |

At each physics step:

1. Convert normalized throttle and braking commands into requests; avoid simultaneous full throttle and brake.
2. Determine requested ICE power and ERS power, respecting a configurable speed-dependent deployment envelope and available energy.
3. Convert requested wheel power to longitudinal force, limited by a low-speed torque/force cap: `F_drive_req = min(F_cap * throttle, efficiency * P_requested / max(speed, v_eps))`.
4. Apply rear-axle combined-grip limits **after** lateral force demand is considered.
5. Blend regenerative and friction braking within axle and total tyre-grip constraints.
6. Compute **actual** energy use/recovery from delivered power, not from requests that were denied by tyre limits.
7. Apply drag, downforce, and resulting tyre forces to the vehicle dynamics.

\[
F_{\mathrm{drag}}=\tfrac12\rho C_dA\,v|v|,\qquad
F_{\mathrm{down}}=\tfrac12\rho C_lA\,v^2.
\]

\[
E_{t+\Delta t}=\mathrm{clip}\left(E_t-(P_{\mathrm{ERS,actual}}-P_{\mathrm{regen,actual}})\Delta t,0,E_{\max}\right).
\]

The ERS deployment envelope is an **illustrative simulation approximation**, not an exact FIA control map. For the first NEAT experiments, ERS deployment should be **rule-based and identical for every agent**; evolving ERS strategy is optional.

### 5.4 Numerical and physical validation

Before evolutionary training, test:

- Straight-line acceleration and speed-dependent force/power limiting.
- Braking distance and no negative speed from numerical overshoot.
- Constant-radius cornering and loss of grip when exceeding physical limits.
- Straight-line stability with zero steering and symmetric conditions.
- Correct steering direction and yaw sign.
- Combined grip: high cornering demand reduces available acceleration/braking.
- ERS energy never becomes negative or exceeds its configured maximum.
- No free energy from regenerative braking; energy accounting matches delivered force.
- Convergence/stability when physics timestep is halved.

## 6. Neural controller and observations

### 6.1 Initial input vector: 16 normalized features

| Indices | Feature | Count |
|---|---|---:|
| 0 | Longitudinal speed `vx` | 1 |
| 1 | Lateral speed `vy` | 1 |
| 2 | Yaw rate `r` | 1 |
| 3 | Sine of heading error relative to reference path | 1 |
| 4 | Signed lateral offset / local half-width | 1 |
| 5–13 | Nine ray distances to track boundaries | 9 |
| 14 | Near look-ahead heading error (~30 m) | 1 |
| 15 | Far look-ahead heading error (~100 m) | 1 |
| **Total** | | **16** |

Suggested sensor-ray angles relative to vehicle heading: `[-90, -67.5, -45, -22.5, 0, 22.5, 45, 67.5, 90]` degrees. Initial maximum ray range: 150 m. Normalize inputs to bounded ranges; specify and test clipping, zero-speed handling, and angle wrapping. The 30/100 m look-ahead values and sensor range are tunable assumptions.

**Scientific caveat:** Reference-path heading/offset/look-ahead observations are derived from a driver's recorded trajectory, not a surveyed centreline. These may bias agents toward that trajectory. A ray-only or reduced-observation ablation is a useful optional comparison.

### 6.2 Initial output vector: 3 actions

| Output | Normalized range | Meaning |
|---|---|---|
| Steering | `[-1, 1]` | Maps to bounded front-wheel steering angle |
| Throttle | `[0, 1]` | Requested drive effort |
| Brake | `[0, 1]` | Requested braking effort |

Network outputs are **commands**, not physical forces. The simulator enforces steering-rate, power, energy, and tyre-grip limits. The NEAT output activation function must be explicitly configured and mapped to these ranges (for example, sigmoid outputs mapped to `[0,1]`, with steering remapped to `[-1,1]`).

**Optional ERS experiment:** add normalized remaining ERS energy as a 17th input and an ERS deployment request as a fourth output.

### 6.3 NEAT implementation

Use [`neat-python`](https://neat-python.readthedocs.io/en/latest/quickstart.html). A NEAT genome describes a network's connections, weights, biases, and topology according to configuration. Unlike a fixed-size weight-vector genetic algorithm, **NEAT can add/remove connections and add nodes**; the number of parameters can vary across genomes.

- Start with `neat.nn.FeedForwardNetwork` and a compact initial topology.
- Fix the input count to 16 and output count to 3 for the core experiments.
- Use NEAT configuration to control initial connectivity, activation, mutation, speciation, population size, and complexity growth.
- Use the same vehicle, track, starting conditions, and evaluation budget for fair comparison within a run.
- Evaluate genomes in isolated environment episodes; assign `genome.fitness` from episode metrics.
- Save the winning genome **and the exact NEAT configuration** required to reconstruct it.

**Do not hardcode a 16→16→16→3 network or 595 parameters as the final NEAT architecture.** That earlier proposal applied to a fixed-topology MLP; it is not a NEAT requirement. A small fixed network may still be used as a separate baseline if useful.

## 7. Fitness and episode rules

The meeting notes emphasize **distance along the track**, followed by **lap time once the agent can complete a lap**, with crashes prevented or penalized. Implement this as a staged objective.

### 7.1 Stage A: learn valid forward progress

- Track progress is measured in metres along the ordered reference path, using the car centre for projection.
- Reward **validated forward progress**, not Euclidean distance from the start and not arbitrary jumps in nearest-point projection.
- Terminate or heavily penalize leaving the track, invalid checkpoint order, wrong-way driving, prolonged inactivity, or exceeding the episode time limit.
- Avoid incentives for driving in circles, oscillating near checkpoints, or exploiting a projection discontinuity.

Illustrative fitness (coefficients to tune):

\[
f_A = \frac{s_{\mathrm{valid}}}{L} - \lambda_{\mathrm{off}}N_{\mathrm{offtrack}} - \lambda_{\mathrm{stall}}T_{\mathrm{stall}}.
\]

Here `s_valid` is validated forward progress and `L` is lap length. If off-track is terminal, the off-track penalty can be a fixed terminal penalty rather than an event count.

### 7.2 Stage B: reward completion and lap time

After completion becomes reasonably frequent, use a completion bonus and time-sensitive score, e.g.:

\[
f_B = f_A + B\,\mathbf{1}_{\mathrm{completed}} + \mathbf{1}_{\mathrm{completed}}\,\alpha\frac{T_{\mathrm{ref}}}{T_{\mathrm{lap}}}.
\]

Select `B` large enough that a completed lap ranks above an incomplete one under the defined score range. Do not grant a lap-time bonus to incomplete laps. Set a reasonable maximum episode duration and a minimum physically plausible lap duration to prevent timing exploits.

**Fitness is not a network output.** It is calculated from the trajectory and assigned to each genome after evaluation. Store component metrics independently of the scalar fitness.

### 7.3 Episode termination

- **Success:** finish gate crossed in the correct direction after ordered checkpoints.
- **Failure:** car leaves the track (full footprint rule), invalid/unrecoverable state, or wrong-way behaviour beyond tolerance.
- **Truncation:** maximum simulated time, maximum steps, or prolonged lack of progress.

Set all thresholds in configuration and log termination reasons. Start every candidate with an equivalent pose and speed; later test multiple starting conditions if generalization is in scope.

## 8. Environment and simulation interface

Expose a Gymnasium-compatible environment even though NEAT does not require Gymnasium:

```python
obs, info = env.reset(seed=seed)
obs, reward, terminated, truncated, info = env.step(action)
```

- Observation shape: `(16,)`, `float32`, bounded and finite.
- Action shape: `(3,)`, normalized continuous commands.
- Proposed controller frequency: **20 Hz** (`dt_control = 0.05 s`).
- Proposed physics frequency: **100 Hz** (`dt_physics = 0.01 s`, five substeps per controller action).
- Training: headless, no Pygame dependency in the update loop.
- Rendering: optional replay/live viewer at ~30–60 FPS; display speed must not change simulation physics.
- `info`: validated progress, checkpoint index, lap time, off-track state, speed, ERS energy, termination reason, and useful diagnostics.

A baseline rule-based controller should be able to call the same environment interface as a NEAT network.

## 9. Proposed Python project structure

```text
f1-neuroevolution/
├── pyproject.toml
├── README.md
├── AGENTS.md
├── docs/
│   └── PROJECT_SPEC.md
├── configs/
│   ├── vehicle.yaml
│   ├── neat.cfg                  # neat-python configuration
│   ├── simulation.yaml
│   └── experiments/
│       ├── monza.yaml
│       └── silverstone.yaml
├── data/
│   └── tracks/
│       ├── raw/
│       └── processed/
├── src/
│   └── f1evo/
│       ├── __init__.py
│       ├── track/
│       │   ├── fastf1_import.py
│       │   ├── geometry.py
│       │   ├── sensors.py
│       │   └── track.py
│       ├── vehicle/
│       │   ├── parameters.py
│       │   ├── dynamics.py
│       │   ├── tyres.py
│       │   ├── aerodynamics.py
│       │   └── powertrain.py
│       ├── simulation/
│       │   ├── environment.py
│       │   ├── observations.py
│       │   ├── rewards.py
│       │   └── termination.py
│       ├── agents/
│       │   ├── neat_controller.py
│       │   └── baseline.py
│       ├── evolution/
│       │   ├── fitness.py
│       │   └── trainer.py
│       ├── optimization/              # OPTIONAL FUTURE STAGE; do not create yet
│       │   └── setup_optimizer.py     # DEAP-based setup search (deferred)
│       ├── rendering/
│       │   └── pygame_viewer.py
│       └── evaluation/
│           ├── metrics.py
│           └── benchmark.py
├── scripts/
│   ├── build_track.py
│   ├── train.py
│   ├── evaluate.py
│   └── replay.py
├── tests/
│   ├── test_track.py
│   ├── test_vehicle.py
│   ├── test_powertrain.py
│   ├── test_environment.py
│   └── test_evolution.py
├── notebooks/
│   └── analysis.ipynb
└── outputs/
    ├── checkpoints/
    ├── metrics/
    └── replays/
```

Create modules as needed; this is the intended separation of concerns, not a requirement to scaffold every empty file immediately. `outputs/`, FastF1 caches, and large raw telemetry should generally be ignored by Git; track provenance and small reproducible processed assets may be versioned as appropriate.

## 10. Dependencies and reuse

| Package | Intended use |
|---|---|
| `numpy` | State arrays, physics, observation processing |
| `scipy` | Interpolation, resampling, numerical helpers |
| `shapely` | Road polygons, containment, geometry validation |
| `fastf1` | Offline circuit-derived position data |
| `neat-python` | Evolution of neural-network weights and topology |
| `gymnasium` | Environment interface and action/observation spaces |
| `pygame` | Optional interactive visualization |
| `matplotlib` | Analysis plots |
| `pyyaml` | Experiment and vehicle configurations |
| `pytest` | Unit and integration testing |

Add `numba` only if profiling identifies a bottleneck. No need for PyTorch or DEAP in the initial NEAT-based implementation. **Do not add DEAP as a dependency or scaffold its optimizer until a separate future milestone is explicitly approved.**

### Relevant references and inspiration

- [FastF1 documentation](https://docs.fastf1.dev/) — session data and lap position samples.
- [FastF1 circuit drawing tutorial](https://python.plainenglish.io/fastf1-tutorials-drawing-a-f1-circuit-5373b3ec45cd) — inspiration for reconstructing a 2D path.
- [neat-python quick start](https://neat-python.readthedocs.io/en/latest/quickstart.html) — population setup and genome evaluation.
- [F1TENTH Gym](https://github.com/f1tenth/f1tenth_gym) — vehicle-simulation/environment design reference, not necessarily the target F1 vehicle model.
- [F1TENTH Benchmarks](https://github.com/hawaii-nc/f1tenth_benchmarks) — benchmarking, metrics, and baseline ideas.
- [Self-driving F1](https://github.com/cangokmen/self-driving-f1) — lightweight racing neuroevolution inspiration.
- [TUM trajectory planning helpers](https://github.com/TUMFTM/trajectory_planning_helpers) — path geometry/curvature inspiration.
- O'Kelly et al., *F1TENTH: An Open-source Evaluation Environment for Continuous Control and Reinforcement Learning* — [paper](https://proceedings.mlr.press/v123/o-kelly20a.html).
- Such et al., *Deep Neuroevolution: Genetic Algorithms Are a Competitive Alternative for Training Deep Neural Networks for Reinforcement Learning* — [paper](https://arxiv.org/abs/1712.06567).
- Evans et al., *Unifying F1TENTH Autonomous Racing: Survey, Methods and Benchmarks* — [paper](https://arxiv.org/abs/2402.18558).

These are candidate references and implementation inspirations, **not automatically approved dependencies**. Inspect repository licenses, API compatibility, and relevant modules before copying code.

## 11. Experimental methodology and reproducibility

### 11.1 Baselines

- **Rule-based driver:** track-following steering and curvature-aware target speed, using the same physics and collision rules.
- **Untrained/random NEAT controllers:** establish the initial performance distribution.
- **Evolved NEAT champion:** measure final trained performance.

### 11.2 Metrics

| Metric | Meaning |
|---|---|
| Lap completion rate | Share of evaluation episodes that complete a valid lap |
| Lap time | Time for valid completed laps only |
| Maximum validated progress | Furthest legal ordered progress reached |
| Off-track failures | Count/rate of boundary violations |
| Mean / maximum speed | Diagnostic driving behaviour |
| Fitness by generation | Evolutionary learning curve |
| Network complexity | Nodes and enabled connections in champions |
| ERS consumption/recovery | Energy-model diagnostic |
| Evaluation runtime | Training efficiency |

### 11.3 Experimental controls

- Record random seeds, code commit, package versions, track source, physics configuration, and NEAT configuration.
- Use repeated independent training seeds; do not draw broad conclusions from one lucky run.
- Evaluate champions under consistent conditions distinct from training randomness when appropriate.
- Use the same evaluation budget for comparisons.
- Keep a held-out track only if cross-track generalization becomes part of the chosen research question.
- Report failures and limitations, including synthetic road geometry and simplified F1 physics.

## 12. Development milestones and acceptance criteria

### M1 — Track preprocessing and geometry

- Load and render a processed circuit from disk.
- Validate closed path, width, polygon geometry, checkpoints, raycasts, and full-car containment.
- **Acceptance:** synthetic unit tests and manual inspection pass; invalid geometry is detected instead of silently accepted.

### M2 — Physics and manual/baseline driving

- Implement kinematic vehicle for initial debugging.
- Add dynamic bicycle model, tyre limits, aero, braking, and powertrain.
- **Acceptance:** acceleration, braking, cornering, and energy tests pass; baseline controller can drive a meaningful portion of the track.

### M3 — Racing environment

- Implement `reset`, `step`, observations, actions, fitness-related metrics, and termination.
- **Acceptance:** identical seeds/configurations yield reproducible trajectories; environment runs headlessly.

### M4 — NEAT training

- Configure `neat-python` for 16 inputs and 3 outputs.
- Implement genome evaluation, checkpoints, champion saving, and replay.
- **Acceptance:** training completes end-to-end and saves analyzable results; investigate whether progress improves over generations.

### M5 — Scientific evaluation

- Compare evolved agents with the baseline over repeated evaluations.
- Report completion, valid lap time, progress, failure rate, network complexity, and runtime.
- **Acceptance:** results are reproducible from saved configurations and seeds.

### Optional M6 — Extension

Choose **one**: cross-track generalization, evolving ERS deployment, or bounded setup optimization. **Setup optimization with DEAP is a future possibility only**, not planned for the current development stage. Do not begin an extension before M1–M5 are working.

### Future stage (not scheduled) — DEAP vehicle setup optimization

The architecture should permit a later **sequential** two-stage experiment without implementing it now:

1. Train a NEAT controller using a fixed baseline car.
2. Freeze and save the selected NEAT controller and its configuration.
3. Use **DEAP** as a separate evolutionary optimizer to propose bounded vehicle **setup** configurations (not new vehicle designs).
4. Evaluate each proposed setup with the frozen controller in the **same** `RacingEnv`, on the same track and under controlled seeds; compare valid completion rates and lap times against the baseline setup.
5. Optionally retrain NEAT on the selected setup to test whether joint adaptation offers an additional benefit. This is a separate experiment, not an assumption that the frozen controller will work optimally with a changed car.

Candidate setup genes, with **illustrative and unvalidated** bounds: aero balance (45–55% front), downforce scale (0.8–1.2×), brake bias (54–62% front), and steering-response scale (0.7–1.0×). Model trade-offs physically: for example, increasing downforce should also incur a plausible drag cost, and brake bias must affect front/rear force allocation. Do not treat these as official F1 regulatory ranges.

**Integration contract:** `VehicleConfig` is a validated, serializable configuration object; `RacingEnv` accepts a vehicle configuration per evaluation and creates independent state; the fitness/metrics interface is algorithm-independent. NEAT owns only the controller genome, and DEAP would own only setup genes. Neither optimizer belongs in the vehicle physics code. A future module could be `src/f1evo/optimization/setup_optimizer.py`, but **do not create or implement it in the current stage**.

A simultaneous NEAT+DEAP co-evolution scheme is an even later, higher-cost research possibility, **not the default plan**. Separate driver and setup optimization first to preserve interpretability.

## 13. Open questions / decisions to confirm

1. **Primary track:** Monza, Silverstone, or a synthetic test circuit first? Recommendation: synthetic debugging track, then one F1-derived track for training.
2. **Track fidelity:** Is a constant-width road around a recorded racing trajectory sufficient for the research claims? Clearly document its limitations.
3. **Collision rule:** terminate on any full-footprint boundary crossing, or permit small recoverable excursions? Recommendation: strict termination initially.
4. **Fitness coefficients and training stages:** choose after observing baseline and early NEAT behaviour; avoid arbitrary unvalidated values.
5. **NEAT settings:** population size, maximum generations, initial connectivity, mutation rates, activation function, and network-complexity constraints must be tuned empirically.
6. **Powertrain calibration:** confirm that assumed ICE/ERS power, drag, tyre grip, and low-speed force cap produce plausible behaviour and numerical stability.
7. **Research extension:** track transfer, ERS optimization, or future DEAP setup optimization; defer selection until a stable baseline exists. DEAP is explicitly not part of the current stage.

## 14. Instructions for Codex implementation

- Read this specification before coding; implement in small, testable milestones.
- Preserve module boundaries and do not embed Pygame in the physics or training loops.
- Use `neat-python` for controller evolution. Do **not** install or implement DEAP now; preserve configuration interfaces that would support a separate DEAP setup optimizer later.
- Keep physical parameters and fitness coefficients configurable, not scattered as magic numbers.
- Add tests for geometry, force limits, energy conservation/accounting, termination, and determinism.
- Do not silently invent official FIA track or vehicle data; label assumptions and cite provenance.
- Do not change the research objective or add advanced physics without documenting the tradeoff.
- Prioritize a functioning end-to-end experiment over detailed but unvalidated realism.
