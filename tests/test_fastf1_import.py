"""Offline importer contract tests; no FastF1 downloads during testing."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M1.7]: Test explicit lap selection and byte-for-byte local raw-CSV rebuilds with mocked/offline data.
# TODO [M1.8]: Test empty laps, invalid drivers, absent telemetry, and all-candidates-rejected error messages.
# TODO [M1.12]: Test offline CLI builds, invalid parameters, and partial-build exit status without network calls.

import hashlib
from datetime import timedelta
from types import SimpleNamespace
import numpy as np
import pandas as pd
from f1evo.track.fastf1_import import build_fastf1


class FakeLap(dict):
    def __init__(self, points, number, time):
        super().__init__(Driver='TST', LapNumber=number, LapTime=timedelta(seconds=time))
        self.positions = pd.DataFrame(points, columns=['X', 'Y'])

    def get_pos_data(self, **kwargs):
        assert kwargs['interpolate_edges'] is True
        return self.positions


class FakeLaps:
    empty = False

    def __init__(self, laps):
        self.laps = laps

    def pick_accurate(self):
        return self

    def pick_quicklaps(self):
        return self

    def sort_values(self, field):
        assert field == 'LapTime'
        return self

    def dropna(self, subset):
        return self

    def iterlaps(self):
        return enumerate(self.laps)


def test_import_units_provenance_and_invalid_lap_fallback(monkeypatch, tmp_path):
    import fastf1
    angles = np.linspace(0, 2*np.pi, 1501)
    metres = np.column_stack([1000*np.cos(angles), 1000*np.sin(angles)])
    metres[-1] = metres[0]
    original = (metres + [150, 75])*10
    invalid = FakeLap(original[:700], 1, 79)
    valid = FakeLap(original, 2, 80)
    session = SimpleNamespace(laps=FakeLaps([invalid, valid]),
                              event={'EventName': 'Italian Grand Prix'})
    session.load = lambda **kwargs: None
    monkeypatch.setattr(fastf1, 'get_session', lambda *args: session)
    monkeypatch.setattr(fastf1.Cache, 'enable_cache', lambda *args: None)
    track = build_fastf1('monza', cache_dir=tmp_path/'cache', raw_dir=tmp_path/'raw')
    assert track.length_m > 6200  # Metres, not decimetres.
    assert np.array_equal(track.points[0], [0, 0])
    assert track.metadata['local_origin_m'] == [1150, 75]
    assert track.metadata['coordinate_scale_to_m'] == 0.1
    assert track.metadata['lap_number'] == 2
    assert track.metadata['rejected_faster_laps']
    raw = next((tmp_path/'raw').glob('*.csv'))
    assert track.metadata['raw_csv_sha256'] == hashlib.sha256(raw.read_bytes()).hexdigest()
