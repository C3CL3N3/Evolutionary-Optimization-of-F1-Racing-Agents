"""Isolated deterministic genome evaluations, checkpoints, and champion/configuration persistence.

Scaffold only: implementation is pending.
"""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M4C.1]: Evaluate every genome in independent reset episodes using the same fixed vehicle, track, starting conditions, and budget.
# TODO [M4C.2]: Assign genome.fitness from completed episode metrics; keep FastF1 and all renderers outside the training loop.
# TODO [M4C.3]: Record training seed, track metadata/hash, vehicle/simulation/fitness settings, NEAT config, code revision, and package versions.
# TODO [M4C.4]: Add generation summaries for best/mean fitness, progress, completion, failures, runtime, and network complexity.
# TODO [M4C.5]: Save periodic population checkpoints and support documented resume semantics.
# TODO [M4C.6]: Save the champion genome, exact NEAT configuration, metrics, and run manifest together.
# TODO [M4C.10]: Profile evaluation runtime only after serial training works; introduce multiprocessing or compilation only for demonstrated bottlenecks.

