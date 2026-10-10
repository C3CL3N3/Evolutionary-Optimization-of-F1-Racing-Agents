"""Train NEAT drivers on a fixed car, headlessly (M4)."""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M4C.7]: Implement scripts/train.py with experiment config, seed, generations, population override, output directory, and resume options.
# TODO [M4C.8]: Run short headless training end to end; reload the champion and reproduce its evaluation under the saved configuration.


import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    parser.exit(2, "Scaffold only: this command is not implemented yet.\n")


if __name__ == "__main__":
    main()
