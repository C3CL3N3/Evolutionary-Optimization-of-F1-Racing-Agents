"""Reusable track geometry; mutable checkpoint/lap state belongs to RacingEnv."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M1.2]: Extend Track.project with previous-progress-aware local projection and continuity handling across the start/finish seam.
# TODO [M1.3]: Add signed lateral offset, wrapped heading error, and near/far look-ahead queries with an explicit tangent/sign convention.
# TODO [M1.4]: Validate finite inputs to pose, projection, interpolation, and ray APIs; reject degenerate tangents and unsupported serialized schemas clearly.

from dataclasses import dataclass
import json
import math
from pathlib import Path
import numpy as np
from shapely.geometry import LineString, Point, Polygon
from .geometry import positive, resample_closed_path, road_polygon


@dataclass(frozen=True)
class Checkpoint:
    index: int
    progress_m: float
    center: tuple[float, float]
    tangent: tuple[float, float]
    endpoints: tuple[tuple[float, float], tuple[float, float]]

    def crossed(self, previous_xy, current_xy):
        """Forward crossing of this finite gate; caller must enforce gate order."""
        before = np.dot(np.subtract(previous_xy, self.center), self.tangent)
        after = np.dot(np.subtract(current_xy, self.center), self.tangent)
        if not (before < 0 <= after):
            return False
        return LineString([previous_xy, current_xy]).intersects(LineString(self.endpoints))


class Track:
    """Closed path and synthetic constant-width road, in SI units.

    Boundary contact is allowed. Any footprint portion outside fails containment.
    Projection is geometry only, NOT validated lap progress or completion.
    """
    def __init__(self, name, points, width_m=12.0, checkpoint_spacing_m=100.0, metadata=None):
        self.name = str(name)
        self.width_m = positive(width_m, 'width_m')
        self.checkpoint_spacing_m = positive(checkpoint_spacing_m, 'checkpoint_spacing_m')
        self.points = np.array(points, dtype=float, copy=True)
        if self.points.ndim != 2 or self.points.shape[1] != 2 or len(self.points) < 5:
            raise ValueError('Expected four vertices plus an explicit closing point')
        if not np.isfinite(self.points).all() or not np.array_equal(self.points[0], self.points[-1]):
            raise ValueError('Track coordinates must be finite and explicitly closed')
        lengths = np.linalg.norm(np.diff(self.points, axis=0), axis=1)
        if np.any(lengths <= 0):
            raise ValueError('Consecutive duplicate vertices')
        self.reference = LineString(self.points)
        self.road = road_polygon(self.points, self.width_m)
        self.length_m = self.reference.length
        self.cumulative_m = np.r_[0.0, np.cumsum(lengths)]
        self.points.setflags(write=False)
        self.cumulative_m.setflags(write=False)
        self.metadata = dict(metadata or {})
        count = max(4, math.ceil(self.length_m / self.checkpoint_spacing_m))
        self.checkpoints = tuple(self._checkpoint(i, i * self.length_m / count) for i in range(count))

    @classmethod
    def from_samples(cls, name, points, *, spacing_m=2.0, max_gap_m=60.0, **kwargs):
        return cls(name, resample_closed_path(points, spacing_m, max_gap_m), **kwargs)

    def point_at(self, progress_m):
        point = self.reference.interpolate(float(progress_m) % self.length_m)
        return point.x, point.y

    def tangent_at(self, progress_m):
        tangent = np.subtract(self.point_at(progress_m + 1), self.point_at(progress_m - 1))
        return tuple(tangent / np.linalg.norm(tangent))

    def _checkpoint(self, index, progress):
        center, tangent = self.point_at(progress), self.tangent_at(progress)
        normal = np.array([-tangent[1], tangent[0]]) * self.width_m / 2
        ends = (tuple(np.array(center) - normal), tuple(np.array(center) + normal))
        return Checkpoint(index, progress, center, tangent, ends)

    def is_on_track(self, x, y):
        return bool(self.road.covers(Point(x, y)))

    def contains_car(self, pose, length=5.2, width=1.9):
        """Entire oriented rectangle; pose = (x, y, heading_rad)."""
        positive(length, 'length')
        positive(width, 'width')
        x, y, heading = pose
        c, s = math.cos(heading), math.sin(heading)
        corners = [(x + c*dx - s*dy, y + s*dx + c*dy)
                   for dx, dy in [(-length/2, -width/2), (length/2, -width/2),
                                  (length/2, width/2), (-length/2, width/2)]]
        return bool(self.road.covers(Polygon(corners)))

    def project(self, x, y):
        """Nearest reference arc length; ordered checkpoint validation is required."""
        return float(self.reference.project(Point(x, y)))

    def raycast(self, x, y, angle, max_range=150.0):
        positive(max_range, 'max_range')
        if not self.is_on_track(x, y):
            return 0.0
        start = Point(x, y)
        ray = LineString([(x, y), (x + max_range*math.cos(angle), y + max_range*math.sin(angle))])
        intersection = self.road.boundary.intersection(ray)
        return max_range if intersection.is_empty else float(start.distance(intersection))

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        document = {'schema_version': 1, 'name': self.name, 'units': 'm',
                    'width_m': self.width_m, 'checkpoint_spacing_m': self.checkpoint_spacing_m,
                    'reference_points': self.points.tolist(), 'metadata': self.metadata}
        path.write_text(json.dumps(document, indent=2, allow_nan=False) + '\n')

    @classmethod
    def load(cls, path):
        document = json.loads(Path(path).read_text())
        if document.get('schema_version') != 1 or document.get('units') != 'm':
            raise ValueError('Unsupported track schema or units')
        return cls(document['name'], document['reference_points'], document['width_m'],
                   document['checkpoint_spacing_m'], document['metadata'])
