"""Staged progress/completion fitness derived from optimizer-independent episode metrics.

Scaffold only: implementation is pending.
"""

# TODO roadmap: TODO.md (task IDs below match the central checklist).
# TODO [M4B.2]: Implement Stage A normalized validated progress with documented off-track/stall penalties.
# TODO [M4B.3]: Implement Stage B completion bonus and valid-lap time scoring; incomplete laps receive no time bonus.
# TODO [M4B.4]: Bound component ranges and choose a completion bonus proving valid completed laps outrank incomplete laps.
# TODO [M4B.5]: Require finite metric inputs and positive plausible completed lap times; reject inconsistent completion data.
# TODO [M4B.7]: Choose stage-transition rules after observing baseline and early training; record coefficients rather than hiding magic numbers.

