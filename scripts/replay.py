"""View a saved trajectory with optional rendering (M4)."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M4D.5]: Implement scripts/replay.py for saved trajectories and champion-generated replays with matching saved configs.
# TODO [M4D.6]: Validate replay fields, source/config compatibility, and helpful missing/corrupt-file errors.


import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    parser.exit(2, "Scaffold only: this command is not implemented yet.\n")


if __name__ == "__main__":
    main()
