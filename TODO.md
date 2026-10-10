# Project TODO — step-by-step implementation roadmap

Based on [the project specification](docs/PROJECT_SPEC.md). Checked items are implemented; unchecked items are planned.

**Current position:** track generation and static viewing work. M1 still needs sensor/path interfaces and additional edge-case coverage. Vehicle physics, episode rules, NEAT training, and scientific evaluation are pending.

**Next action:** finish M1.1–M1.4 and their tests, then implement VehicleConfig (M2A). Work through the steps in order; complete the acceptance check before moving to the next dependent step.

Each task has a stable ID. `# TODO [ID]` comments in Python files, configuration templates, packaging metadata, and ignore rules refer to this checklist. Check off the central task and remove its local comment when the work is validated.

Generated JSON/CSV tracks, images (including f1_car.png), cache files, .gitkeep placeholders, IDE preferences, and governing instruction/specification files are not annotated. Their handling and future work are tracked here through the responsible source files and documentation tasks.

## Rules for every step

- Keep the vehicle and setup fixed across initial NEAT genomes; evolve network weights and topology only.
- Use SI units, fixed timesteps, deterministic seeds, and independent episode state.
- Keep Track, VehicleConfig, RacingEnv, and evaluation metrics independent of optimizers.
- Import telemetry offline; never call FastF1 inside training or evaluation episodes.
- Make rendering optional; display speed must never change physics.
- Describe synthetic roads, vehicle parameters, and ERS maps as assumptions, not official FIA accuracy.
- Add meaningful tests with each implemented milestone; a placeholder file is not a completed feature.
- Add dependencies only for a demonstrated need and record versions for experiments.

## Already completed

- [x] Create the Python package scaffold and separate track, vehicle, simulation, controller, evolution, rendering, and evaluation modules.
- [x] Store the development specification in docs/PROJECT_SPEC.md and preserve the original root copy.
- [x] Use libraries from the BiCS conda environment for track building and visualization.
- [x] Generate deterministic circle, oval, and technical synthetic tracks.
- [x] Import Monza 2024 qualifying NOR lap 11 and Silverstone 2024 qualifying HAM lap 24 through FastF1.
- [x] Convert recorded X/Y positions to metres and save selected-lap provenance, raw-data hashes, and rejected-faster-lap diagnostics.
- [x] Discard nonfinite/consecutive duplicate samples and reject large gaps, crossing reference paths, and detected road merges.
- [x] Build closed approximately 2 m sampled reference paths with assumed 12 m constant-width roads.
- [x] Implement geometric arc-length projection, tangent/interpolation queries, ordered gate definitions, and directional gate-crossing predicates.
- [x] Implement full oriented rectangular footprint containment and nearest-boundary raycasts.
- [x] Save/reload processed JSON tracks independently of FastF1 and network access.
- [x] Add static Matplotlib previews and a five-track overview with road, reference path, gates, and direction.
- [x] Add build_track.py and view_tracks.py CLI entry points.
- [x] Pass the existing 21 geometry/importer/headless-viewer tests; this is not validation of physics or episode progress.

## Implementation sequence

### Step 0 — Development setup and shared contracts

**Dependency:** Complete before adding physics; keep using the BiCS environment.

- [ ] **F0.1** — Record a reproducible dependency/environment snapshot and add dependencies only when the next milestone needs them. Files: `pyproject.toml`.
- [ ] **F0.2** — Verify BiCS interpreter selection and pytest discovery in the IDE; document one working setup command sequence.
- [ ] **F0.3** — Define configuration schemas, project-relative path resolution, units, defaults, and clear validation errors. Files: `configs/simulation.yaml`, `configs/experiments/monza.yaml`, `configs/experiments/silverstone.yaml`.
- [ ] **F0.4** — Expose stable public APIs from package initializers once their implementations exist; keep imports free of downloads, windows, and mutable episode state.
- [ ] **F0.5** — Keep generated telemetry, caches, checkpoints, metrics, and replays ignored; retain small processed tracks and provenance deliberately. Files: `.gitignore`.
- [ ] **F0.6** — Maintain this roadmap and local TODO comments together; mark a task complete only with implementation and relevant validation.
- [ ] **F0.7** — Start recording code revision and package versions for reproducible experiments; choose version control before training runs.

**Acceptance:** A student can select BiCS, run the current track tests, and locate configs/data using documented paths.

### Step 1 — Finish track geometry and sensor interfaces

**Dependency:** Depends on F0. Existing track generation and static plots are the starting point.

- [ ] **M1.1** — Implement the sensors module as a shared nine-ray sampler using Track.raycast, configurable angles, and a maximum range. Files: `src/f1evo/track/sensors.py`.
- [ ] **M1.2** — Extend Track.project with previous-progress-aware local projection and continuity handling across the start/finish seam. Files: `src/f1evo/track/track.py`.
- [ ] **M1.3** — Add signed lateral offset, wrapped heading error, and near/far look-ahead queries with an explicit tangent/sign convention. Files: `src/f1evo/track/track.py`, `src/f1evo/track/sensors.py`.
- [ ] **M1.4** — Validate finite inputs to pose, projection, interpolation, and ray APIs; reject degenerate tangents and unsupported serialized schemas clearly. Files: `src/f1evo/track/track.py`.
- [ ] **M1.5** — Make preprocessing gap limits configurable and record removed sample counts, closure gaps, and processing package versions in provenance. Files: `src/f1evo/track/geometry.py`, `src/f1evo/track/fastf1_import.py`.
- [ ] **M1.6** — Review conservative road-merge detection on tight bends and nearby parallel segments; document accepted/rejected examples without silently repairing tracks. Files: `src/f1evo/track/geometry.py`.
- [ ] **M1.7** — Add explicit recorded-lap selection and a local raw-CSV rebuild path so exact source laps can be reproduced without downloading a session again. Files: `src/f1evo/track/fastf1_import.py`, `scripts/build_track.py`, `tests/test_fastf1_import.py`.
- [ ] **M1.8** — Handle unavailable sessions, missing telemetry, invalid driver/lap selections, and exhausted candidate laps with actionable errors. Files: `src/f1evo/track/fastf1_import.py`, `scripts/build_track.py`, `tests/test_fastf1_import.py`.
- [ ] **M1.9** — Keep synthetic generators deterministic; expose only the dimensions needed for controlled geometry tests and record them in metadata. Files: `src/f1evo/track/synthetic.py`.
- [ ] **M1.10** — Test seam projection, signed offsets, angle wrapping, nine rays, exact boundary contact, and difficult nearby-section topology. Files: `tests/test_track.py`.
- [ ] **M1.11** — Test repeated gate crossings and gate endpoint cases; reserve mutable gate order and lap state for the environment. Files: `tests/test_track.py`.
- [ ] **M1.12** — Add CLI checks for invalid width/spacing, no matching files, and partial build failures; preserve a clear offline build/view workflow. Files: `scripts/build_track.py`, `scripts/view_tracks.py`, `tests/test_fastf1_import.py`.
- [ ] **M1.13** — Add an optional diagnostic view of a selected pose, footprint, rays, and checkpoint numbers for geometry inspection. Files: `src/f1evo/rendering/track_viewer.py`, `scripts/view_tracks.py`.
- [ ] **M1.14** — Document raw-CSV rebuild instructions, telemetry limitations, and the consistent boundary-contact rule.

**Acceptance:** Saved tracks and static plots work offline; geometry/sensor interfaces and difficult seam/boundary cases pass focused tests.

### Step 2 — Validate the fixed car configuration

**Dependency:** Depends on F0 and the basic M1 geometry interfaces.

- [ ] **M2A.1** — Implement an optimizer-independent immutable VehicleConfig with SI fields matching configs/vehicle.yaml. Files: `src/f1evo/vehicle/parameters.py`.
- [ ] **M2A.2** — Load/save VehicleConfig through YAML and plain serializable dictionaries without sharing mutable state between evaluations. Files: `src/f1evo/vehicle/parameters.py`.
- [ ] **M2A.3** — Validate finite positive physical dimensions, mass/inertia/stiffness, axle distances, and lf + lr = wheelbase. Files: `src/f1evo/vehicle/parameters.py`, `configs/vehicle.yaml`.
- [ ] **M2A.4** — Validate steering limits, efficiency ranges, friction coefficients, force/power caps, and ERS capacity bounds. Files: `src/f1evo/vehicle/parameters.py`, `configs/vehicle.yaml`.
- [ ] **M2A.5** — Add explicit fixed baseline brake allocation, aero load allocation, low-speed threshold, and ERS deployment settings where the physics needs them. Files: `src/f1evo/vehicle/parameters.py`, `configs/vehicle.yaml`.
- [ ] **M2A.6** — Test invalid configurations, round-trip serialization, and independent instances; label all baseline values as modelling assumptions.

**Acceptance:** VehicleConfig rejects invalid physical inputs and survives serialization while staying independent of optimizers.

### Step 3 — Implement a simple kinematic car first

**Dependency:** Depends on M2A. Use circle/oval before real circuits.

- [ ] **M2B.1** — Define VehicleState with world pose, body-frame vx/vy, yaw rate, steering angle, and ERS energy. Files: `src/f1evo/vehicle/dynamics.py`.
- [ ] **M2B.2** — Define normalized steering/throttle/brake commands and a deterministic rule resolving simultaneous drive and brake requests. Files: `src/f1evo/vehicle/dynamics.py`.
- [ ] **M2B.3** — Implement reset and a fixed-step kinematic bicycle update with explicit world/body coordinate and yaw conventions. Files: `src/f1evo/vehicle/dynamics.py`.
- [ ] **M2B.4** — Apply steering angle and steering rate limits at every physics step. Files: `src/f1evo/vehicle/dynamics.py`.
- [ ] **M2B.5** — Prevent reverse motion from numerical braking overshoot and reject nonfinite vehicle state. Files: `src/f1evo/vehicle/dynamics.py`.
- [ ] **M2B.6** — Test straight motion, steering/yaw direction, constant-radius motion, stop behaviour, and timestep convergence.
- [ ] **M2B.7** — Create a short deterministic driving smoke run with footprint checks and a saved trajectory before adding dynamic tyres.

**Acceptance:** The kinematic car moves, turns, brakes, and records a repeatable footprint-safe smoke trajectory.

### Step 4 — Add tyres, aero, and ICE/ERS powertrain

**Dependency:** Depends on M2B; force and energy calculations must be validated before dynamic driving.

- [ ] **M2C.1** — Compute static front/rear normal loads from mass, axle geometry, and configurable aero load allocation. Files: `src/f1evo/vehicle/tyres.py`.
- [ ] **M2C.2** — Compute front/rear slip angles and linear lateral forces with one documented sign convention. Files: `src/f1evo/vehicle/tyres.py`.
- [ ] **M2C.3** — Enforce axle combined-grip ellipses; lateral demand must reduce available drive and braking force. Files: `src/f1evo/vehicle/tyres.py`.
- [ ] **M2C.4** — Implement quadratic drag opposing longitudinal motion and nonnegative speed-dependent downforce. Files: `src/f1evo/vehicle/aerodynamics.py`.
- [ ] **M2C.5** — Convert throttle to ICE wheel power and force with drivetrain efficiency and a low-speed force cap. Files: `src/f1evo/vehicle/powertrain.py`.
- [ ] **M2C.6** — Implement a deterministic rule-based ERS speed envelope and energy-limited deployment identical for every driver. Files: `src/f1evo/vehicle/powertrain.py`.
- [ ] **M2C.7** — Blend rear regenerative braking and configurable front/rear friction braking within tyre and power limits. Files: `src/f1evo/vehicle/powertrain.py`.
- [ ] **M2C.8** — Calculate actual delivered ICE/ERS/regen power after grip limits and separate mechanical and electrical energy. Files: `src/f1evo/vehicle/powertrain.py`.
- [ ] **M2C.9** — Update ERS using delivered power and efficiency; prevent empty-battery deployment, overfill, and free regeneration. Files: `src/f1evo/vehicle/powertrain.py`.
- [ ] **M2C.10** — Test power/force caps, speed dependence, combined grip, regen-only/friction-only cases, and energy accounting over many steps.

**Acceptance:** Combined force limits and delivered-power ERS accounting pass before integration into dynamic driving.

### Step 5 — Add the dynamic bicycle model

**Dependency:** Depends on validated M2C components; preserve the kinematic model for low-speed debugging.

- [ ] **M2D.1** — Integrate vx, vy, yaw rate, heading, and world pose with the documented 3-DOF force equations. Files: `src/f1evo/vehicle/dynamics.py`.
- [ ] **M2D.2** — Use a fixed physics timestep and semi-implicit Euler; make the update order explicit. Files: `src/f1evo/vehicle/dynamics.py`.
- [ ] **M2D.3** — Blend or fall back to kinematic motion near zero speed to avoid slip-angle singularities. Files: `src/f1evo/vehicle/dynamics.py`.
- [ ] **M2D.4** — Advance powertrain energy from the forces actually delivered by the integrated vehicle model. Files: `src/f1evo/vehicle/dynamics.py`.
- [ ] **M2D.5** — Validate acceleration curves, braking distance, zero-steering stability, turning direction, and loss of grip.
- [ ] **M2D.6** — Repeat representative trajectories at half the physics timestep and define acceptable convergence/stability tolerances.
- [ ] **M2D.7** — Calibrate the fixed baseline car against plausible behaviour and document calibration plots and assumptions. Files: `configs/vehicle.yaml`.

**Acceptance:** Acceleration/braking/cornering/stability and timestep-convergence checks pass with documented fixed-car calibration.

### Step 6 — Implement a deterministic headless environment

**Dependency:** Depends on M1 interfaces and M2 validation. Training is still deferred.

- [ ] **M3A.1** — Implement RacingEnv with a processed Track and VehicleConfig; create independent vehicle/episode state for each instance. Files: `src/f1evo/simulation/environment.py`.
- [ ] **M3A.2** — Implement Gymnasium-compatible reset(seed=...) and step(action) plus defined action/observation spaces. Files: `src/f1evo/simulation/environment.py`.
- [ ] **M3A.3** — Validate that control_dt is an integer multiple of physics_dt; begin with 0.05 s control and 0.01 s physics. Files: `src/f1evo/simulation/environment.py`, `configs/simulation.yaml`.
- [ ] **M3A.4** — Validate finite actions and shapes, clip normalized commands consistently, and define behaviour after episode end. Files: `src/f1evo/simulation/environment.py`.
- [ ] **M3A.5** — Reset all counters, timers, progress, checkpoints, and ERS to equivalent configured starting conditions. Files: `src/f1evo/simulation/environment.py`.
- [ ] **M3A.6** — Build exactly 16 finite float32 observations in the specified order: five state/path features, nine rays, and two look-aheads. Files: `src/f1evo/simulation/observations.py`.
- [ ] **M3A.7** — Define and test bounded normalization scales, clipping, heading wrapping, and zero-speed handling. Files: `src/f1evo/simulation/observations.py`, `configs/simulation.yaml`.
- [ ] **M3A.8** — Check full-footprint containment and gate crossings at every physics substep, including multiple gates within a control step. Files: `src/f1evo/simulation/environment.py`.
- [ ] **M3A.9** — Return observations, reward, terminated, truncated, and diagnostics without rendering or data downloads. Files: `src/f1evo/simulation/environment.py`.
- [ ] **M3A.10** — Include validated progress, next checkpoint, elapsed time, completion, speed, ERS, and termination reason in info. Files: `src/f1evo/simulation/environment.py`.

**Acceptance:** The environment exposes the promised shapes/timing and runs headlessly with independent reset state.

### Step 7 — Secure progress, completion, and episode rules

**Dependency:** Depends on M3A. Complete before assigning genome fitness.

- [ ] **M3B.1** — Track continuous unwrapped progress bounded by feasible per-step displacement; reject jumps to nearby unrelated sections. Files: `src/f1evo/simulation/environment.py`.
- [ ] **M3B.2** — Require directional checkpoint crossings in order and prevent repeat/oscillation rewards. Files: `src/f1evo/simulation/environment.py`.
- [ ] **M3B.3** — Declare completion only after every required gate and a forward finish crossing; starting on the finish line must not complete a lap. Files: `src/f1evo/simulation/environment.py`, `src/f1evo/simulation/termination.py`.
- [ ] **M3B.4** — Track maximum validated forward progress separately from raw projected progress and travelled Euclidean distance. Files: `src/f1evo/simulation/environment.py`.
- [ ] **M3B.5** — Terminate off-track, invalid-state, and persistent wrong-way episodes; truncate time/step-limit and stalled episodes. Files: `src/f1evo/simulation/termination.py`.
- [ ] **M3B.6** — Add configurable wrong-way tolerance, inactivity window, minimum progress, maximum episode duration/steps, and plausible minimum lap time. Files: `src/f1evo/simulation/termination.py`, `configs/simulation.yaml`.
- [ ] **M3B.7** — Implement per-step progress rewards with configurable terminal penalties and independently logged reward components. Files: `src/f1evo/simulation/rewards.py`, `configs/simulation.yaml`.
- [ ] **M3B.8** — Test shortcutting, teleportation, reversing, checkpoint skips, finish-line oscillation, stalling, and implausible lap timing.
- [ ] **M3B.9** — Test equal-seed trajectory reproducibility, independent environments, headless imports, and control/physics timing.

**Acceptance:** Illegal checkpoints, shortcuts, loops, timing exploits, and invalid states cannot produce valid completed laps.

### Step 8 — Add a baseline driver and trajectory recording

**Dependency:** Depends on M3A/M3B. Establish a driveable reference before NEAT.

- [ ] **M3C.1** — Define a common controller observation-to-action interface usable by baseline and NEAT drivers. Files: `src/f1evo/agents/baseline.py`, `src/f1evo/agents/neat_controller.py`.
- [ ] **M3C.2** — Implement track-following steering using normalized offset, heading error, and look-ahead features. Files: `src/f1evo/agents/baseline.py`.
- [ ] **M3C.3** — Use curvature/look-ahead demand for a bounded target speed and choose throttle/brake without simultaneous full commands. Files: `src/f1evo/agents/baseline.py`.
- [ ] **M3C.4** — Keep baseline tuning parameters fixed within each experiment and record them with results. Files: `src/f1evo/agents/baseline.py`, `configs/experiments/monza.yaml`, `configs/experiments/silverstone.yaml`.
- [ ] **M3C.5** — Demonstrate repeatable baseline progress on synthetic tracks and then Monza/Silverstone; log failures as well as successes. Files: `src/f1evo/evaluation/benchmark.py`.
- [ ] **M3C.6** — Define an optimizer-independent replay schema containing timestamps, poses, controls, progress, checkpoints, and ERS diagnostics. Files: `src/f1evo/simulation/environment.py`.
- [ ] **M3C.7** — Record baseline trajectories and lap/progress/failure summaries without requiring a viewer. Files: `src/f1evo/evaluation/benchmark.py`.

**Acceptance:** The baseline drives a meaningful repeatable portion of a track and emits a saved, analyzable trajectory.

### Step 9 — Configure and connect NEAT

**Dependency:** Depends on a validated environment and baseline. Evolve only the driver.

- [ ] **M4A.1** — Choose and record the neat-python version; replace neat.cfg with a complete loadable configuration. Files: `configs/neat.cfg`, `pyproject.toml`.
- [ ] **M4A.2** — Use 16 inputs, 3 outputs, feed-forward networks, and explicitly mapped sigmoid actions. Files: `src/f1evo/agents/neat_controller.py`, `configs/neat.cfg`.
- [ ] **M4A.3** — Configure initial connectivity, weight/bias mutation, node/connection mutation, speciation, stagnation, reproduction, and population size. Files: `configs/neat.cfg`.
- [ ] **M4A.4** — Keep topology evolution configurable; do not impose the discarded fixed multilayer architecture. Files: `configs/neat.cfg`.
- [ ] **M4A.5** — Implement the NEAT controller adapter; validate network dimensions and finite outputs. Files: `src/f1evo/agents/neat_controller.py`.
- [ ] **M4A.6** — Test exact steering/throttle/brake mapping and champion reconstruction from genome plus exact configuration.

**Acceptance:** neat.cfg loads with the recorded neat-python version and the controller produces three correctly mapped commands.

### Step 10 — Define robust staged episode fitness

**Dependency:** Depends on M3B metrics and rules; keep metrics independent of optimizers.

- [ ] **M4B.1** — Define typed episode metrics separating progress, completion, valid lap time, penalties, speed, and energy. Files: `src/f1evo/evaluation/metrics.py`.
- [ ] **M4B.2** — Implement Stage A normalized validated progress with documented off-track/stall penalties. Files: `src/f1evo/evolution/fitness.py`.
- [ ] **M4B.3** — Implement Stage B completion bonus and valid-lap time scoring; incomplete laps receive no time bonus. Files: `src/f1evo/evolution/fitness.py`.
- [ ] **M4B.4** — Bound component ranges and choose a completion bonus proving valid completed laps outrank incomplete laps. Files: `src/f1evo/evolution/fitness.py`.
- [ ] **M4B.5** — Require finite metric inputs and positive plausible completed lap times; reject inconsistent completion data. Files: `src/f1evo/evolution/fitness.py`.
- [ ] **M4B.6** — Test fitness against loops, oscillations, invalid checkpoints, off-track shortcuts, timeout cases, and timing exploits.
- [ ] **M4B.7** — Choose stage-transition rules after observing baseline and early training; record coefficients rather than hiding magic numbers. Files: `src/f1evo/evolution/fitness.py`, `configs/simulation.yaml`.

**Acceptance:** Fitness ranks valid completion above incomplete episodes and passes explicit exploit tests.

### Step 11 — Train and persist reproducible champions

**Dependency:** Depends on M4A/M4B; begin with small serial smoke runs.

- [ ] **M4C.1** — Evaluate every genome in independent reset episodes using the same fixed vehicle, track, starting conditions, and budget. Files: `src/f1evo/evolution/trainer.py`.
- [ ] **M4C.2** — Assign genome.fitness from completed episode metrics; keep FastF1 and all renderers outside the training loop. Files: `src/f1evo/evolution/trainer.py`.
- [ ] **M4C.3** — Record training seed, track metadata/hash, vehicle/simulation/fitness settings, NEAT config, code revision, and package versions. Files: `src/f1evo/evolution/trainer.py`, `configs/experiments/monza.yaml`, `configs/experiments/silverstone.yaml`.
- [ ] **M4C.4** — Add generation summaries for best/mean fitness, progress, completion, failures, runtime, and network complexity. Files: `src/f1evo/evolution/trainer.py`.
- [ ] **M4C.5** — Save periodic population checkpoints and support documented resume semantics. Files: `src/f1evo/evolution/trainer.py`.
- [ ] **M4C.6** — Save the champion genome, exact NEAT configuration, metrics, and run manifest together. Files: `src/f1evo/evolution/trainer.py`.
- [ ] **M4C.7** — Implement scripts/train.py with experiment config, seed, generations, population override, output directory, and resume options. Files: `scripts/train.py`.
- [ ] **M4C.8** — Run short headless training end to end; reload the champion and reproduce its evaluation under the saved configuration. Files: `scripts/train.py`.
- [ ] **M4C.9** — Test configuration equality across genomes, isolated mutable state, checkpoint recovery, and deterministic serial evaluation.
- [ ] **M4C.10** — Profile evaluation runtime only after serial training works; introduce multiprocessing or compilation only for demonstrated bottlenecks. Files: `src/f1evo/evolution/trainer.py`.

**Acceptance:** A serial headless smoke run saves checkpoints, a reconstructable champion, metrics, and exact configurations.

### Step 12 — Add optional live/replay visualization

**Dependency:** Depends on the M3C replay schema; visualization may never alter physics timing.

- [ ] **M4D.1** — Implement an optional Pygame viewer loading processed geometry and rendering an oriented vehicle footprint. Files: `src/f1evo/rendering/pygame_viewer.py`.
- [ ] **M4D.2** — Verify f1_car.png provenance/permission and orientation before optional sprite use; scale it to the physical footprint and retain a rectangle fallback. Files: `src/f1evo/rendering/pygame_viewer.py`.
- [ ] **M4D.3** — Display speed, simulated time, progress, checkpoint, ERS, and episode status with optional sensor overlays. Files: `src/f1evo/rendering/pygame_viewer.py`.
- [ ] **M4D.4** — Implement pause, restart, and display-speed controls independent of fixed simulation/replay timestamps. Files: `src/f1evo/rendering/pygame_viewer.py`.
- [ ] **M4D.5** — Implement scripts/replay.py for saved trajectories and champion-generated replays with matching saved configs. Files: `scripts/replay.py`.
- [ ] **M4D.6** — Validate replay fields, source/config compatibility, and helpful missing/corrupt-file errors. Files: `scripts/replay.py`.
- [ ] **M4D.7** — Verify training and evaluation work when Pygame is unavailable; inspect at least one baseline and champion replay. Files: `src/f1evo/rendering/pygame_viewer.py`.

**Acceptance:** A saved trajectory can be replayed visually with pause/speed controls while training remains viewer-independent.

### Step 13 — Run repeatable scientific evaluation

**Dependency:** Depends on working M4 training, persisted champions, and baseline metrics.

- [ ] **M5A.1** — Define a benchmark protocol using the same car, track, seeds/starts, collision rules, and evaluation budgets for all compared drivers. Files: `src/f1evo/evaluation/benchmark.py`, `configs/experiments/monza.yaml`, `configs/experiments/silverstone.yaml`.
- [ ] **M5A.2** — Compare the rule-based baseline, untrained/random NEAT controllers, and evolved champions. Files: `src/f1evo/evaluation/benchmark.py`.
- [ ] **M5A.3** — Run repeated independent training seeds and separate champion evaluation from training randomness. Files: `src/f1evo/evaluation/benchmark.py`, `configs/experiments/monza.yaml`, `configs/experiments/silverstone.yaml`.
- [ ] **M5A.4** — Report completion rate, completed-lap times only, maximum legal progress, failure counts/reasons, and mean/max speed. Files: `src/f1evo/evaluation/metrics.py`.
- [ ] **M5A.5** — Report ERS use/recovery, nodes/enabled connections, per-generation fitness, and evaluation/training runtime. Files: `src/f1evo/evaluation/metrics.py`.
- [ ] **M5A.6** — Handle zero-completion experiments explicitly; never invent lap times or silently exclude failures. Files: `src/f1evo/evaluation/metrics.py`.
- [ ] **M5A.7** — Serialize per-episode and aggregate metrics to stable CSV/JSON outputs with complete provenance. Files: `src/f1evo/evaluation/metrics.py`, `scripts/evaluate.py`.
- [ ] **M5A.8** — Implement scripts/evaluate.py with experiment, driver/champion, seed set, repetitions, and output selection. Files: `scripts/evaluate.py`.
- [ ] **M5A.9** — Test aggregation, missing results, completed-only lap timing, consistent comparisons, and reproducible saved result loading. Files: `src/f1evo/evaluation/benchmark.py`.
- [ ] **M5A.10** — Keep cross-track generalization outside the core experiment unless separately selected as an extension.

**Acceptance:** Repeated comparisons retain all episodes and produce reproducible per-episode and aggregate results.

### Step 14 — Analysis, report, and reproducibility handoff

**Dependency:** Depends on M5A results; distinguish measured results from assumptions.

- [ ] **M5B.1** — Create an analysis notebook loading saved results only; avoid hidden training or downloading side effects.
- [ ] **M5B.2** — Plot learning curves, completion rate across seeds, lap-time/progress distributions, network complexity, and runtime.
- [ ] **M5B.3** — Produce shareable figures with units, labels, legends, and uncertainty summaries appropriate to the sample size.
- [ ] **M5B.4** — Document experiment settings, repeated-run variability, baseline tuning, and reasons for failed episodes.
- [ ] **M5B.5** — Describe synthetic roads, telemetry bias, simplified physics, ERS approximations, and calibration limits without claiming FIA accuracy.
- [ ] **M5B.6** — Update README with working build/train/evaluate/replay commands and artifact locations.
- [ ] **M5B.7** — Document how another student can reconstruct a champion and regenerate metrics from its saved run manifest.
- [ ] **M5B.8** — Run the milestone acceptance checks from a reproducible environment and retain their results with the final report.
- [ ] **M5B.9** — Update the specification deliberately when accepted modelling decisions change; keep the retained root copy consistent with docs/PROJECT_SPEC.md.

**Acceptance:** Another student can reconstruct a champion, regenerate results, and understand limitations from the report.

## Tests to create with their implementation

These files do not exist yet. Create them when the corresponding implementation is ready, rather than adding empty or skipped tests.

| Planned file | Implement alongside | Required evidence |
| --- | --- | --- |
| `tests/test_vehicle_config.py` | M2A | Validation, SI dimensions, round-trip config, independence |
| `tests/test_vehicle.py` | M2B/M2D | Motion/yaw signs, stop behaviour, dynamic stability, timestep convergence |
| `tests/test_tyres.py` | M2C | Slip signs, axle grip limits, combined grip |
| `tests/test_aerodynamics.py` | M2C | Drag direction, quadratic growth, nonnegative downforce |
| `tests/test_powertrain.py` | M2C/M2D | Caps, empty/full ERS, actual energy accounting, no free regen |
| `tests/test_observations.py` | M3A | Feature order, shape/dtype, finite bounds, wrapping |
| `tests/test_environment.py` | M3A/M3B | Independent state, timing, determinism, gates, completion, termination |
| `tests/test_baseline.py` | M3C | Legal bounded commands and repeatable progress |
| `tests/test_evolution.py` | M4A/M4B/M4C | Config loading, action mapping, fitness exploits, checkpoint/champion reload |
| `tests/test_metrics.py` | M5A | Aggregate metrics, zero completions, completed-only lap times |
| `tests/test_replay.py` | M4D | Replay schema, timestamps, source/config validation, headless loading |

## Source-file checklist index

Package `__init__.py` files also carry F0.4: expose only stable APIs and keep imports free of work.

| File | Local task IDs |
| --- | --- |
| [.gitignore](.gitignore) | F0.5 |
| [configs/experiments/monza.yaml](configs/experiments/monza.yaml) | F0.3, M3C.4, M4C.3, M5A.1, M5A.3 |
| [configs/experiments/silverstone.yaml](configs/experiments/silverstone.yaml) | F0.3, M3C.4, M4C.3, M5A.1, M5A.3 |
| [configs/neat.cfg](configs/neat.cfg) | M4A.1, M4A.2, M4A.3, M4A.4 |
| [configs/simulation.yaml](configs/simulation.yaml) | F0.3, M3A.3, M3A.7, M3B.6, M3B.7, M4B.7 |
| [configs/vehicle.yaml](configs/vehicle.yaml) | M2A.3, M2A.4, M2A.5, M2D.7 |
| [pyproject.toml](pyproject.toml) | F0.1, M4A.1 |
| [scripts/build_track.py](scripts/build_track.py) | M1.7, M1.8, M1.12 |
| [scripts/evaluate.py](scripts/evaluate.py) | M5A.8, M5A.7 |
| [scripts/replay.py](scripts/replay.py) | M4D.5, M4D.6 |
| [scripts/train.py](scripts/train.py) | M4C.7, M4C.8 |
| [scripts/view_tracks.py](scripts/view_tracks.py) | M1.12, M1.13 |
| [src/f1evo/agents/baseline.py](src/f1evo/agents/baseline.py) | M3C.1, M3C.2, M3C.3, M3C.4 |
| [src/f1evo/agents/neat_controller.py](src/f1evo/agents/neat_controller.py) | M3C.1, M4A.2, M4A.5 |
| [src/f1evo/evaluation/benchmark.py](src/f1evo/evaluation/benchmark.py) | M3C.5, M3C.7, M5A.1, M5A.2, M5A.3, M5A.9 |
| [src/f1evo/evaluation/metrics.py](src/f1evo/evaluation/metrics.py) | M4B.1, M5A.4, M5A.5, M5A.6, M5A.7 |
| [src/f1evo/evolution/fitness.py](src/f1evo/evolution/fitness.py) | M4B.2, M4B.3, M4B.4, M4B.5, M4B.7 |
| [src/f1evo/evolution/trainer.py](src/f1evo/evolution/trainer.py) | M4C.1, M4C.2, M4C.3, M4C.4, M4C.5, M4C.6, M4C.10 |
| [src/f1evo/rendering/pygame_viewer.py](src/f1evo/rendering/pygame_viewer.py) | M4D.1, M4D.2, M4D.3, M4D.4, M4D.7 |
| [src/f1evo/rendering/track_viewer.py](src/f1evo/rendering/track_viewer.py) | M1.13 |
| [src/f1evo/simulation/environment.py](src/f1evo/simulation/environment.py) | M3A.1, M3A.2, M3A.3, M3A.4, M3A.5, M3A.8, M3A.9, M3A.10, M3B.1, M3B.2, M3B.3, M3B.4, M3C.6 |
| [src/f1evo/simulation/observations.py](src/f1evo/simulation/observations.py) | M3A.6, M3A.7 |
| [src/f1evo/simulation/rewards.py](src/f1evo/simulation/rewards.py) | M3B.7 |
| [src/f1evo/simulation/termination.py](src/f1evo/simulation/termination.py) | M3B.3, M3B.5, M3B.6 |
| [src/f1evo/track/fastf1_import.py](src/f1evo/track/fastf1_import.py) | M1.5, M1.7, M1.8 |
| [src/f1evo/track/geometry.py](src/f1evo/track/geometry.py) | M1.5, M1.6 |
| [src/f1evo/track/sensors.py](src/f1evo/track/sensors.py) | M1.1, M1.3 |
| [src/f1evo/track/synthetic.py](src/f1evo/track/synthetic.py) | M1.9 |
| [src/f1evo/track/track.py](src/f1evo/track/track.py) | M1.2, M1.3, M1.4 |
| [src/f1evo/vehicle/aerodynamics.py](src/f1evo/vehicle/aerodynamics.py) | M2C.4 |
| [src/f1evo/vehicle/dynamics.py](src/f1evo/vehicle/dynamics.py) | M2B.1, M2B.2, M2B.3, M2B.4, M2B.5, M2D.1, M2D.2, M2D.3, M2D.4 |
| [src/f1evo/vehicle/parameters.py](src/f1evo/vehicle/parameters.py) | M2A.1, M2A.2, M2A.3, M2A.4, M2A.5 |
| [src/f1evo/vehicle/powertrain.py](src/f1evo/vehicle/powertrain.py) | M2C.5, M2C.6, M2C.7, M2C.8, M2C.9 |
| [src/f1evo/vehicle/tyres.py](src/f1evo/vehicle/tyres.py) | M2C.1, M2C.2, M2C.3 |
| [tests/test_fastf1_import.py](tests/test_fastf1_import.py) | M1.7, M1.8, M1.12 |
| [tests/test_track.py](tests/test_track.py) | M1.10, M1.11 |

## Data, artifacts, and documentation

- [ ] **D1** — Preserve small processed track JSONs and source metadata as reproducible inputs; avoid adding TODO keys to the track schema.
- [ ] **D2** — Keep raw telemetry and FastF1 caches local; provide a documented source-lap rebuild path through M1.7.
- [ ] **D3** — Save population checkpoints and reconstructable champions under `outputs/checkpoints/` through M4C.
- [ ] **D4** — Save per-episode/generation CSV/JSON metrics and run manifests under `outputs/metrics/` through M4C/M5A.
- [ ] **D5** — Save time-indexed trajectories under `outputs/replays/` through M3C/M4D.
- [ ] **D6** — Create `notebooks/analysis.ipynb` only when saved experiment results exist (M5B.1).
- [ ] **D7** — Record the supplied car image provenance and intended rendering scale before use (M4D.2).
- [ ] **D8** — Keep README commands, tests/README coverage, and this roadmap accurate after each milestone.

## Deferred extensions — outside the current checklist

M1–M5 must work first. Extensions require a separate later request and a scoped decision.

- Cross-track transfer or observation ablations: optional future experiment.
- Learned ERS: optional future 17-input/4-output experiment; the initial driver remains 16-input/3-output with rule-based ERS.
- DEAP setup optimization: deferred. Do not add its dependency, package, optimizer, or experiments now.
- If setup optimization is later requested: train the fixed-car NEAT driver, freeze a champion, then evaluate bounded setups with the same independent RacingEnv and metrics.
- Simultaneous driver/setup co-evolution, opponents, detailed suspension/thermal tyres, and regulation-accurate 2026 systems are not initial scope.

## Milestone completion record

| Milestone | Current status | Evidence required to close |
| --- | --- | --- |
| M1 tracks | Partially implemented; 21 existing tests passed previously | Remaining geometry/sensor interfaces and edge-case tests |
| M2 physics | Pending | Configuration, kinematic/dynamic motion, grip, aero, braking, ERS tests; baseline smoke trajectory |
| M3 environment | Pending | Reproducible headless episodes, observations, safe progress and termination |
| M4 NEAT | Pending | Reconstructable champion, saved config/checkpoint, headless training and replay |
| M5 evaluation | Pending | Repeated controlled comparisons and reproducible report artifacts |

Add run IDs, relevant commands, results, and accepted modelling decisions here as milestones are completed.
