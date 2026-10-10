"""Deterministic debugging circuits, not replicas of real F1 tracks."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M1.9]: Keep synthetic generators deterministic; expose only the dimensions needed for controlled geometry tests and record them in metadata.

import numpy as np
from .track import Track

NAMES = ('circle', 'oval', 'technical')


def build_synthetic(name, width_m=12.0, spacing_m=2.0):
    t = np.linspace(0, 2*np.pi, 1501)
    if name == 'circle':
        x, y = 100*np.cos(t), 100*np.sin(t)
    elif name == 'oval':
        x, y = 220*np.cos(t), 100*np.sin(t)
    elif name == 'technical':
        radius = 180 + 35*np.cos(3*t) + 15*np.sin(5*t)
        x, y = radius*np.cos(t), 0.75*radius*np.sin(t)
    else:
        raise ValueError(f'Unknown synthetic track: {name}')
    points = np.column_stack([x, y])
    points[-1] = points[0]
    return Track.from_samples(name, points, width_m=width_m, spacing_m=spacing_m,
        metadata={'source': 'synthetic', 'generator': 'analytic-v1',
                  'description': 'Deterministic test circuit; arbitrary start and CCW direction',
                  'sample_spacing_target_m': spacing_m,
                  'road_assumption': 'Synthetic constant-width road'})
