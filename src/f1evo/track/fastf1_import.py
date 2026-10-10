"""Offline recorded-lap import. Training must never call this importer."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M1.5]: Make preprocessing gap limits configurable and record removed sample counts, closure gaps, and processing package versions in provenance.
# TODO [M1.7]: Add explicit recorded-lap selection and a local raw-CSV rebuild path so exact source laps can be reproduced without downloading a session again.
# TODO [M1.8]: Handle unavailable sessions, missing telemetry, invalid driver/lap selections, and exhausted candidate laps with actionable errors.

import hashlib
import json
from pathlib import Path
import numpy as np
from .track import Track

EVENTS = {'monza': 'Italian Grand Prix', 'silverstone': 'British Grand Prix'}


def build_fastf1(name, *, year=2024, session_code='Q', driver=None,
                 cache_dir='data/fastf1_cache', raw_dir='data/tracks/raw',
                 width_m=12.0, spacing_m=2.0):
    import fastf1  # Lazy: processed tracks never need FastF1 or network access.
    cache = Path(cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache))
    session = fastf1.get_session(year, EVENTS[name], session_code)
    session.load(telemetry=True, weather=False, messages=False)
    laps = session.laps.pick_accurate().pick_quicklaps()
    if driver:
        laps = laps.pick_drivers(driver)
    laps = laps.sort_values('LapTime').dropna(subset=['LapTime'])
    if laps.empty:
        raise ValueError('No accurately timed valid laps available')
    rejected = []
    for _, lap in laps.iterlaps():
        positions = lap.get_pos_data(interpolate_edges=True)
        xy = positions[['X', 'Y']].to_numpy(dtype=float) * 0.1
        # FastF1 3.8 documents X/Y in tenths of a metre.
        if len(xy) < 4 or not np.isfinite(xy[0]).all():
            rejected.append('Missing valid position samples')
            continue
        origin = xy[0].copy()
        xy -= origin
        csv = positions.to_csv(index=False)
        metadata = {'source': 'fastf1', 'fastf1_version': fastf1.__version__,
                    'year': year, 'event': str(session.event['EventName']),
                    'session': session_code, 'driver': str(lap['Driver']),
                    'lap_number': int(lap['LapNumber']),
                    'lap_time_s': float(lap['LapTime'].total_seconds()),
                    'position_units_original': '1/10 m', 'coordinate_scale_to_m': 0.1,
                    'local_origin_m': origin.tolist(), 'raw_sample_count': len(xy),
                    'raw_csv_sha256': hashlib.sha256(csv.encode()).hexdigest(),
                    'sample_spacing_target_m': spacing_m, 'smoothing': 'none',
                    'selection_rule': 'Fastest accurately timed quick lap passing geometry validation',
                    'rejected_faster_laps': rejected.copy(),
                    'road_assumption': 'Synthetic constant-width road around recorded driving trajectory',
                    'provenance_url': 'https://docs.fastf1.dev/',
                    'boundary_contact': 'allowed; any footprint outside road is off-track'}
        try:
            track = Track.from_samples(name, xy, width_m=width_m, spacing_m=spacing_m,
                                        metadata=metadata)
            if not 4000 <= track.length_m <= 7000:
                raise ValueError(f'Implausible lap length: {track.length_m:.0f} m')
        except ValueError as error:
            rejected.append(f"{lap['Driver']} lap {lap['LapNumber']}: {error}")
            continue
        raw = Path(raw_dir)
        raw.mkdir(parents=True, exist_ok=True)
        stem = f"{name}_{year}_{session_code}_{lap['Driver']}_lap{int(lap['LapNumber'])}"
        (raw / f'{stem}.csv').write_text(csv)
        (raw / f'{stem}.json').write_text(json.dumps(metadata, indent=2) + '\n')
        return track
    raise ValueError('No lap passed track validation:\n' + '\n'.join(rejected[:10]))
