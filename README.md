# F1 neuroevolution

Python bachelor semester project: evolve F1-inspired racing drivers with `neat-python`.
NEAT evolves controller weights and topology; the vehicle and setup stay fixed.
Track preprocessing and a static track viewer are implemented. Vehicle physics,
the racing environment, and training remain scaffolds.
All physical values are initial modelling assumptions, not official FIA data.

## Setup

Requires Python 3.11 or newer. Use the existing `BiCS` conda environment:

```sh
conda activate BiCS
```

Track building needs NumPy, Shapely 2, and FastF1; plots need Matplotlib, and tests
need pytest. These are available in `BiCS`. For a fresh environment, install
`python -m pip install -e '.[tracks,analysis,dev]'`.

Validated with NumPy 2.5.3, Shapely 2.1.2, FastF1 3.8.3, Matplotlib 3.11.2,
pytest 9.1.1, and pandas 2.3.3. Installing FastF1 in `BiCS` changed pandas from
3.0.6 to 2.3.3 to satisfy FastF1's pandas <3 requirement.

Dependencies are opt-in by milestone. For geometry/environment work, install
`.[simulation]`; offline telemetry preprocessing adds `.[tracks]`, evolution adds
`.[training]`, and optional visualization/analysis use `.[rendering,analysis]`.
No dependency installation is necessary to inspect the scaffold or use script help.

## Tracks and simplest visualization

Five processed tracks and their PNG previews are in `data/tracks/processed/`:

| Track | Approximate reference length | Source |
| --- | --- | --- |
| Circle | 628 m | Analytic 100 m radius, for basic geometry/physics debugging |
| Oval | 1,041 m | Analytic ellipse, for varying curvature |
| Technical | 1,111 m | Analytic lobed loop, for tighter bends |
| Monza | 5,760 m | 2024 qualifying, NOR lap 11 |
| Silverstone | 5,835 m | 2024 qualifying, HAM lap 24 |

```sh
# View the saved tracks in a simple Matplotlib window; also save overview.png.
python scripts/view_tracks.py --show

# Save the overview without opening a window or downloading any data.
python scripts/view_tracks.py

# Regenerate synthetic tracks offline.
python scripts/build_track.py --track synthetic

# Build all five tracks; the first run downloads qualifying telemetry.
python scripts/build_track.py --track all

# Build one recorded track with optional source selection.
python scripts/build_track.py --track monza --year 2024 --session Q

# Plot one saved track.
python scripts/view_tracks.py data/tracks/processed/monza.json --show

python -m pytest -q
```

Plots show the filled road, dashed reference path, cyan checkpoint gates, red
start/finish gate, and forward direction. Axes use metres and equal scaling.
All roads are synthetic, with an assumed 12 m total width and approximately
2 m reference-point spacing. F1-derived paths are recorded driving trajectories,
not official centrelines or boundaries. Telemetry is converted from tenths of a
metre; coordinates are translated to the selected lap's starting position.
The start gate uses the lap boundary returned by FastF1, not a surveyed gate.

The importer chooses the fastest accurately timed quick lap that passes geometry
validation. It rejects large gaps, self-crossings, invalid road topology, and
merges between nonadjacent sections; it does not smooth corners or silently
repair invalid tracks. Validity checks are conservative geometric checks, not
a guarantee of real-world circuit accuracy. Source metadata and a raw-data hash
are saved in each JSON. Raw CSVs and the FastF1 cache remain local and ignored
by Git. Loading a processed track and viewing it require no network or FastF1.
For Silverstone, the faster RUS lap 25 failed the conservative road-merge check;
HAM lap 24 was selected instead. Rejected faster laps are recorded in metadata.

`Track` supports footprint containment, directional gates, nearest geometric
projection, and boundary raycasts. Boundary contact is allowed; any portion of
the car footprint outside the road fails containment. Ordered checkpoint state,
continuous validated progress, and lap completion must be added to `RacingEnv`
in M3; geometric projection by itself must never be used as valid fitness.

## Layout

- `docs/PROJECT_SPEC.md`: canonical development specification; root copy retained from the original folder.
- `configs/`: vehicle assumptions, simulation settings, NEAT design template, and experiment templates.
- `src/f1evo/track/`: offline import, geometry, checkpoints, progress, and sensors.
- `src/f1evo/vehicle/`: configuration, dynamics, tyres, aerodynamics, and powertrain.
- `src/f1evo/simulation/`: independent episode state, observations, rewards, and termination.
- `src/f1evo/agents/`: NEAT and baseline controller adapters.
- `src/f1evo/evolution/`: genome fitness and training orchestration.
- `src/f1evo/evaluation/`: optimizer-independent metrics and repeatable benchmarks.
- `src/f1evo/rendering/`: optional viewer, isolated from training and physics.
- `scripts/`: entry points for track building, training, evaluation, and replay.
- `tests/`: validation plan; executable tests arrive with implementations.
- `data/tracks/`: raw telemetry and reusable processed tracks.
- `outputs/`: generated checkpoints, metrics, and replays (ignored by Git).
- `notebooks/`: future analysis notebooks.

Remaining scaffold modules document their responsibilities. YAML files define proposed settings;
loaders and validators are pending. `configs/neat.cfg` is explicitly a design
template and must be completed before training. Training, evaluation, and replay
scripts support `--help` and fail clearly until implemented.

## Development order

See [TODO.md](TODO.md) for the detailed step-by-step checklist. Each Python file
and configuration template contains matching task IDs for its remaining work.

1. **M1:** synthetic track first; geometry, checkpoints, sensors, and containment.
2. **M2:** kinematic then dynamic bicycle physics, grip, aero, braking, and ERS.
3. **M3:** deterministic headless environment with 16 inputs and 3 actions.
4. **M4:** isolated NEAT evaluations, checkpoints, champion saving, and replay.
5. **M5:** repeated baseline/champion comparisons and reproducible reporting.

Use SI units and fixed physics timesteps. FastF1 runs only during offline track
preprocessing. Rendering never drives physics timing. VehicleConfig, RacingEnv,
and metrics must remain independent of optimizers. DEAP and setup optimization
are deferred and are not scaffolded.

See `tests/README.md` for the validation required before training. Geometry and
headless plot tests exist; physics and environment tests arrive with their milestones.

## Documentation TODOs

- [ ] **M1.14** — Add raw-CSV rebuild instructions when the importer supports them.
- [ ] **M5B.6** — Add verified training, evaluation, and replay commands as they become available.
- [ ] **M5B.7** — Document champion reconstruction and reproducibility from a saved run manifest.
- [ ] **F0.6** — Keep completed features and local TODOs synchronized with [TODO.md](TODO.md).
