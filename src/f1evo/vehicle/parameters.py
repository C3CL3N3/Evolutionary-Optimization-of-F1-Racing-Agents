"""Validated, serializable VehicleConfig with fixed F1-inspired assumptions shared across evaluations.

Scaffold only: implementation is pending.
"""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M2A.1]: Implement an optimizer-independent immutable VehicleConfig with SI fields matching configs/vehicle.yaml.
# TODO [M2A.2]: Load/save VehicleConfig through YAML and plain serializable dictionaries without sharing mutable state between evaluations.
# TODO [M2A.3]: Validate finite positive physical dimensions, mass/inertia/stiffness, axle distances, and lf + lr = wheelbase.
# TODO [M2A.4]: Validate steering limits, efficiency ranges, friction coefficients, force/power caps, and ERS capacity bounds.
# TODO [M2A.5]: Add explicit fixed baseline brake allocation, aero load allocation, low-speed threshold, and ERS deployment settings where the physics needs them.

