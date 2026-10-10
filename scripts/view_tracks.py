"""Plot saved tracks without downloading telemetry or running a simulator."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M1.12]: Validate selected file paths and output options; report missing/corrupt tracks clearly.
# TODO [M1.13]: Expose optional pose/footprint/ray overlays and checkpoint numbers through CLI flags.

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', type=Path, help='Processed JSON tracks; defaults to all')
    parser.add_argument('--output', type=Path, default=ROOT/'data/tracks/processed/overview.png')
    parser.add_argument('--show', action='store_true', help='Also open a Matplotlib window')
    parser.add_argument('--no-checkpoints', action='store_true')
    args = parser.parse_args()
    from f1evo.track.track import Track
    from f1evo.rendering.track_viewer import view_tracks
    paths = args.paths or sorted((ROOT/'data/tracks/processed').glob('*.json'))
    if not paths:
        parser.error('No processed tracks found. Run scripts/build_track.py first.')
    try:
        view_tracks([Track.load(path) for path in paths], args.output, args.show, not args.no_checkpoints)
    except (ValueError, OSError) as error:
        parser.exit(1, f'{error}\n')
    print(f'Saved {args.output}')


if __name__ == '__main__':
    main()
