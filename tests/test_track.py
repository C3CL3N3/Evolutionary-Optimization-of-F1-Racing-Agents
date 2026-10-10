"""Geometry and visualization validation using deterministic synthetic circuits."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M1.10]: Test seam projection, signed offsets, angle wrapping, nine rays, exact boundary contact, and difficult nearby-section topology.
# TODO [M1.11]: Test repeated gate crossings and gate endpoint cases; reserve mutable gate order and lap state for the environment.

import json
import math
import numpy as np
import pytest
from f1evo.track.geometry import resample_closed_path
from f1evo.track.synthetic import NAMES, build_synthetic
from f1evo.track.track import Track
from f1evo.rendering.track_viewer import view_tracks


@pytest.fixture(scope='module')
def circle():
    return build_synthetic('circle')


@pytest.mark.parametrize('name', NAMES)
def test_synthetic_geometry(name):
    track = build_synthetic(name)
    assert track.reference.is_ring
    assert track.road.is_valid
    assert len(track.road.interiors) == 1
    assert np.array_equal(track.points[0], track.points[-1])
    assert np.max(np.linalg.norm(np.diff(track.points, axis=0), axis=1)) <= 2.001
    assert track.road.area == pytest.approx(track.length_m*12, rel=0.005)
    assert all(track.is_on_track(*point) for point in track.points[::20])


def test_circle_length_and_width(circle):
    assert circle.length_m == pytest.approx(2*math.pi*100, rel=0.0001)
    assert circle.is_on_track(100, 0)
    assert not circle.is_on_track(0, 0)
    assert not circle.is_on_track(107, 0)


def test_full_oriented_footprint(circle):
    assert circle.contains_car((100, 0, math.pi/2))
    assert circle.is_on_track(104, 0)
    assert circle.contains_car((104, 0, math.pi/2))
    assert not circle.contains_car((104, 0, 0))
    assert not circle.contains_car((105.5, 0, math.pi/2))


def test_raycast_nearest_boundary_and_range(circle):
    assert circle.raycast(100, 0, 0) == pytest.approx(6, abs=0.01)
    assert circle.raycast(100, 0, math.pi) == pytest.approx(6, abs=0.01)
    assert circle.raycast(100, 0, math.pi/2, 5) == 5
    assert circle.raycast(0, 0, 0) == 0


def test_checkpoint_order_direction_and_finite_gate(circle):
    gates = circle.checkpoints
    assert [gate.index for gate in gates] == list(range(len(gates)))
    assert np.all(np.diff([gate.progress_m for gate in gates]) > 0)
    assert gates[0].progress_m == 0
    for gate in gates:
        assert np.linalg.norm(np.subtract(*gate.endpoints)) == pytest.approx(12)
        center, tangent = np.array(gate.center), np.array(gate.tangent)
        assert gate.crossed(center-tangent, center+tangent)
        assert not gate.crossed(center+tangent, center-tangent)
        assert not gate.crossed(center+tangent, center+2*tangent)
        normal = np.array([-tangent[1], tangent[0]])
        assert not gate.crossed(center+20*normal-tangent, center+20*normal+tangent)


def test_serialization_round_trip(circle, tmp_path):
    path = tmp_path/'track.json'
    circle.save(path)
    loaded = Track.load(path)
    assert np.array_equal(loaded.points, circle.points)
    assert loaded.road.equals_exact(circle.road, 1e-9)
    assert loaded.metadata == circle.metadata
    assert loaded.checkpoints == circle.checkpoints
    with pytest.raises(ValueError):
        loaded.points[0, 0] = 42


def test_reject_unknown_file_units(circle, tmp_path):
    path = tmp_path/'track.json'
    circle.save(path)
    document = json.loads(path.read_text())
    document['units'] = 'decimetres'
    path.write_text(json.dumps(document))
    with pytest.raises(ValueError, match='schema or units'):
        Track.load(path)


def test_invalid_and_duplicate_samples_are_cleaned(circle):
    points = np.insert(circle.points, 20, [[np.nan, 0], circle.points[19]], axis=0)
    clean = resample_closed_path(points)
    assert np.isfinite(clean).all()
    assert np.all(np.linalg.norm(np.diff(clean, axis=0), axis=1) > 0)


def test_reject_incomplete_lap(circle):
    with pytest.raises(ValueError, match='Incomplete lap'):
        resample_closed_path(circle.points[:len(circle.points)//2])


def test_reject_internal_gap(circle):
    points = np.vstack([circle.points[:10], circle.points[100:]])
    with pytest.raises(ValueError, match='Discontinuous path'):
        resample_closed_path(points)


def test_reject_crossing():
    with pytest.raises(ValueError, match='crosses'):
        resample_closed_path([[0, 0], [20, 20], [0, 20], [20, 0], [0, 0]])


def test_reject_road_overlap():
    t = np.linspace(0, 2*np.pi, 601)
    points = np.column_stack([100*np.cos(t), 4*np.sin(t)])
    points[-1] = points[0]
    with pytest.raises(ValueError, match='annulus|merges'):
        Track.from_samples('too-narrow', points)


@pytest.mark.parametrize('width', [0, -12, float('nan'), float('inf')])
def test_reject_invalid_width(width):
    with pytest.raises(ValueError, match='positive and finite'):
        build_synthetic('circle', width_m=width)


def test_projection_and_wrap(circle):
    xy = circle.point_at(circle.length_m/4)
    assert circle.project(*xy) == pytest.approx(circle.length_m/4)
    assert circle.point_at(circle.length_m+20) == pytest.approx(circle.point_at(20))
    assert circle.tangent_at(0) == pytest.approx((0, 1), abs=0.001)


def test_headless_viewer(circle, tmp_path):
    path = tmp_path/'preview.png'
    view_tracks([circle], path)
    assert path.read_bytes().startswith(b'\x89PNG\r\n\x1a\n')
