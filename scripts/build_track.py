"""Build synthetic tracks and/or recorded FastF1 laps offline, then save plots."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M1.7]: Add explicit lap and local raw-CSV input options for exact offline rebuilds.
# TODO [M1.8]: Report unavailable sessions, invalid source selections, and missing telemetry clearly.
# TODO [M1.12]: Validate finite positive width/spacing before downloads and test partial-build failure behaviour.

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--track', choices=['all', 'synthetic', 'circle', 'oval', 'technical', 'monza', 'silverstone'], default='synthetic')
    parser.add_argument('--year', type=int, default=2024)
    parser.add_argument('--session', default='Q')
    parser.add_argument('--driver', help='Optional FastF1 driver code, e.g. VER')
    parser.add_argument('--width', type=float, default=12.0, help='Total road width [m]')
    parser.add_argument('--spacing', type=float, default=2.0, help='Target reference sample spacing [m]')
    parser.add_argument('--output-dir', type=Path, default=ROOT/'data/tracks/processed')
    parser.add_argument('--no-plot', action='store_true')
    args = parser.parse_args()
    from f1evo.track.synthetic import NAMES, build_synthetic
    from f1evo.track.fastf1_import import EVENTS, build_fastf1
    names = list(NAMES) if args.track in ('synthetic', 'all') else [args.track]
    if args.track == 'all':
        names += list(EVENTS)
    errors = []
    for name in names:
        try:
            if name in NAMES:
                track = build_synthetic(name, args.width, args.spacing)
            else:
                track = build_fastf1(name, year=args.year, session_code=args.session,
                                    driver=args.driver, width_m=args.width, spacing_m=args.spacing,
                                    cache_dir=ROOT/'data/fastf1_cache', raw_dir=ROOT/'data/tracks/raw')
            path = args.output_dir/f'{name}.json'
            track.save(path)
            print(f'Saved {path}: {track.length_m:.1f} m, {len(track.checkpoints)} gates', flush=True)
            if not args.no_plot:
                from f1evo.rendering.track_viewer import view_tracks
                view_tracks([track], args.output_dir/f'{name}.png')
        except (ValueError, RuntimeError, OSError) as error:
            errors.append(f'{name}: {error}')
    if errors:
        parser.exit(1, '\n'.join(errors) + '\n')


if __name__ == '__main__':
    main()
