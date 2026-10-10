"""RacingEnv owns independent episode state and exposes Gymnasium-compatible reset/step methods.

Scaffold only: implementation is pending.
"""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M3A.1]: Implement RacingEnv with a processed Track and VehicleConfig; create independent vehicle/episode state for each instance.
# TODO [M3A.2]: Implement Gymnasium-compatible reset(seed=...) and step(action) plus defined action/observation spaces.
# TODO [M3A.3]: Validate that control_dt is an integer multiple of physics_dt; begin with 0.05 s control and 0.01 s physics.
# TODO [M3A.4]: Validate finite actions and shapes, clip normalized commands consistently, and define behaviour after episode end.
# TODO [M3A.5]: Reset all counters, timers, progress, checkpoints, and ERS to equivalent configured starting conditions.
# TODO [M3A.8]: Check full-footprint containment and gate crossings at every physics substep, including multiple gates within a control step.
# TODO [M3A.9]: Return observations, reward, terminated, truncated, and diagnostics without rendering or data downloads.
# TODO [M3A.10]: Include validated progress, next checkpoint, elapsed time, completion, speed, ERS, and termination reason in info.
# TODO [M3B.1]: Track continuous unwrapped progress bounded by feasible per-step displacement; reject jumps to nearby unrelated sections.
# TODO [M3B.2]: Require directional checkpoint crossings in order and prevent repeat/oscillation rewards.
# TODO [M3B.3]: Declare completion only after every required gate and a forward finish crossing; starting on the finish line must not complete a lap.
# TODO [M3B.4]: Track maximum validated forward progress separately from raw projected progress and travelled Euclidean distance.
# TODO [M3C.6]: Define an optimizer-independent replay schema containing timestamps, poses, controls, progress, checkpoints, and ERS diagnostics.

