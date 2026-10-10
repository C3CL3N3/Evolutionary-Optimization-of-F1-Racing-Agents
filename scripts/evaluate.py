"""Compare baseline and evolved drivers reproducibly (M5)."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M5A.8]: Implement scripts/evaluate.py with experiment, driver/champion, seed set, repetitions, and output selection.
# TODO [M5A.7]: Serialize per-episode and aggregate metrics to stable CSV/JSON outputs with complete provenance.


import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    parser.exit(2, "Scaffold only: this command is not implemented yet.\n")


if __name__ == "__main__":
    main()
