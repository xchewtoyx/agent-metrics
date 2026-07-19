#!/usr/bin/env python3
"""Pre-review self-check.

Runs the mechanizable review gates before you request review — the same checks
CI runs (`black`, `ruff`, `pytest`, which now includes the invariant tests in
`tests/test_invariants.py`) — then prints the checklist items that cannot be
mechanized. Exits non-zero if any gate fails.

Usage: python scripts/review.py

See docs/review-checklist.md for the full checklist.
"""

from __future__ import annotations

import subprocess
import sys

_GATES: list[tuple[str, list[str]]] = [
    ("black --check", [sys.executable, "-m", "black", "--check", "."]),
    ("ruff", [sys.executable, "-m", "ruff", "check", "."]),
    ("pytest", [sys.executable, "-m", "pytest"]),
]

_MANUAL_REMINDERS = (
    "Renamed a public symbol? Grep docs/, README.md, CHANGELOG.md for the old name.",
    "Docstrings and CLI help describe current behavior, not aspirations.",
    "Load-bearing change? Add a change contract and a CHANGELOG entry.",
)


def main() -> int:
    failures = []
    for name, cmd in _GATES:
        print(f"→ {name}")
        if subprocess.run(cmd).returncode != 0:
            failures.append(name)

    print("\nManual checklist (not mechanizable):")
    for reminder in _MANUAL_REMINDERS:
        print(f"  - {reminder}")

    if failures:
        print(f"\nFAILED: {', '.join(failures)}")
        return 1
    print("\nAll gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
