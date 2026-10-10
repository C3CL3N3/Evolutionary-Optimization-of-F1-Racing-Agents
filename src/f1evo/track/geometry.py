"""Closed-path preprocessing and validation in metres."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M1.5]: Make preprocessing gap limits configurable and record removed sample counts, closure gaps, and processing package versions in provenance.
# TODO [M1.6]: Review conservative road-merge detection on tight bends and nearby parallel segments; document accepted/rejected examples without silently repairing tracks.

import math
import numpy as np
from shapely.geometry import LineString, Polygon
from shapely.strtree import STRtree


def positive(value, name):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be positive and finite')
    return value


def resample_closed_path(points, spacing_m=2.0, max_gap_m=60.0):
    """Remove invalid/duplicate samples, reject gaps, and resample without smoothing."""
    positive(spacing_m, 'spacing_m')
    positive(max_gap_m, 'max_gap_m')
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2:
        raise ValueError('Expected an (N, 2) array of metre coordinates')
    points = points[np.isfinite(points).all(axis=1)]
    if len(points) < 4:
        raise ValueError('At least four finite samples are required')
    keep = np.r_[True, np.linalg.norm(np.diff(points, axis=0), axis=1) > 1e-6]
    points = points[keep]
    if len(points) < 4:
        raise ValueError('Too few distinct samples')
    gap = np.linalg.norm(points[-1] - points[0])
    if gap > max_gap_m:
        raise ValueError(f'Incomplete lap: closing gap is {gap:.1f} m')
    if gap > 1e-6:
        points = np.vstack([points, points[0]])
    else:
        points[-1] = points[0]
    lengths = np.linalg.norm(np.diff(points, axis=0), axis=1)
    if lengths.max() > max_gap_m:
        raise ValueError(f'Discontinuous path: sample gap is {lengths.max():.1f} m')
    line = LineString(points)
    if not line.is_simple:
        raise ValueError('Reference path crosses or touches itself')
    cumulative = np.r_[0.0, np.cumsum(lengths)]
    samples = np.linspace(0, cumulative[-1], max(4, math.ceil(line.length / spacing_m)) + 1)
    result = np.column_stack([np.interp(samples, cumulative, points[:, i]) for i in range(2)])
    result[-1] = result[0]
    return result


def road_polygon(points, width_m):
    """Reject crossings and nonlocal road merges rather than silently repairing them."""
    positive(width_m, 'width_m')
    line = LineString(points)
    if not line.is_ring or line.length <= 4 * width_m:
        raise ValueError('Reference must be a sufficiently long simple closed loop')
    road = line.buffer(width_m / 2, quad_segs=8)
    if not isinstance(road, Polygon) or not road.is_valid or len(road.interiors) != 1:
        raise ValueError('Road must be a valid annulus; width merges or collapses sections')
    segments = [LineString([a, b]) for a, b in zip(points[:-1], points[1:])]
    lengths = np.array([segment.length for segment in segments])
    midpoints = np.cumsum(lengths) - lengths / 2
    tree = STRtree(segments)
    for i, segment in enumerate(segments):
        for j in tree.query(segment.buffer(width_m)):
            if j <= i:
                continue
            separation = abs(midpoints[j] - midpoints[i])
            separation = min(separation, line.length - separation)
            if separation > 2 * width_m and segment.distance(segments[j]) < width_m - 1e-6:
                raise ValueError('Road width merges nonadjacent path sections')
    return road
