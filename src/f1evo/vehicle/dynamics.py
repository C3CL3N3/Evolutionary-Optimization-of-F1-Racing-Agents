"""VehicleState and fixed-step kinematic, then dynamic bicycle integration in SI units.

Scaffold only: implementation is pending.
"""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M2B.1]: Define VehicleState with world pose, body-frame vx/vy, yaw rate, steering angle, and ERS energy.
# TODO [M2B.2]: Define normalized steering/throttle/brake commands and a deterministic rule resolving simultaneous drive and brake requests.
# TODO [M2B.3]: Implement reset and a fixed-step kinematic bicycle update with explicit world/body coordinate and yaw conventions.
# TODO [M2B.4]: Apply steering angle and steering rate limits at every physics step.
# TODO [M2B.5]: Prevent reverse motion from numerical braking overshoot and reject nonfinite vehicle state.
# TODO [M2D.1]: Integrate vx, vy, yaw rate, heading, and world pose with the documented 3-DOF force equations.
# TODO [M2D.2]: Use a fixed physics timestep and semi-implicit Euler; make the update order explicit.
# TODO [M2D.3]: Blend or fall back to kinematic motion near zero speed to avoid slip-angle singularities.
# TODO [M2D.4]: Advance powertrain energy from the forces actually delivered by the integrated vehicle model.

