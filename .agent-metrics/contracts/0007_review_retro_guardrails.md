# Change Contract: 0007 - Guardrails from the PR Review Retro

- **ID**: `0007_review_retro_guardrails`
- **Issue**: n/a (retro-driven harness improvement)
- **Component**: Tests / Docs / Process
- **Created**: 2026-07-18
- **Status**: Proposed

## Observed Failure Evidence

A retro over the ~19 review threads on PRs #10 and #16 found recurring classes of
defect, all caught by the reviewer rather than the local gate:

- **Doc/comment overclaim and doc↔code drift** (largest category): help text and
  docstrings saying "structural" for a metric-agnostic recorder; a `build_*`
  "No I/O" claim on a function that reads git/env; a CHANGELOG export not in
  `__all__`; a contract referencing a renamed symbol.
- **Error handling narrower than the documented robustness — the same bug
  twice**: `SOURCE_DATE_EPOCH` suppressed only `ValueError` (missed
  `OverflowError`/`OSError`) in #10, and `get_git_metadata` caught only
  `FileNotFoundError` (missed the `OSError` family) in #16.
- **Single-source-of-truth drift**: `tool_version` hard-coded in four builders.

Every one of these shipped with **100% line coverage**, which proved lines ran,
not that the documented guarantees held.

## Inferred Root Cause

The test suite optimized for coverage percentage instead of asserting contracts,
and the recurring findings were never encoded into the harness, so the identical
mistake pattern reappeared one PR later.

## Proposed Change

1. Add `tests/test_invariants.py` pinning documented guarantees: single-source
   version, graceful degradation across the whole `OSError`/`SubprocessError`
   family, strict/deterministic JSON round-trip, the documented envelope shape,
   `__all__` importability, and api-conventions symbol references.
2. Encode the recurring findings into `docs/review-checklist.md` and
   `docs/api-conventions.md`: catch base exceptions for degrade-gracefully
   functions (with a family test), single-source derived defaults, prose accuracy,
   rename reference-grep, and "documented guarantees are tested; coverage is not
   the bar".

## Affected Component

- `tests/test_invariants.py`: invariant/contract tests.
- `docs/review-checklist.md`, `docs/api-conventions.md`: encoded guardrails.

## Predicted Fixes

- The recurring narrow-exception bug is caught by a family test before review.
- Record-shape and version drift are caught mechanically.
- Reviewers (human and bot) stop re-litigating settled classes because the rules
  are written down.

## Regression Risks

- **Doc-parsing fragility**: the api-conventions symbol test parses the verb
  table; it asserts a non-empty token set so a format change fails loudly rather
  than passing vacuously.

## Verification Plan

1. **Checks**: `black`, `ruff`, and `pytest` pass at 100% coverage.
2. **Mutation sanity**: the family test fails if `get_git_metadata` narrows its
   `except` back to `FileNotFoundError`; the version test fails on a hard-coded
   default.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: The invariant tests pin the guarantees, the guardrails are documented,
  and all checks pass.
- **IMPROVE**: Coverage of guarantees is right but needs extension (e.g. executable
  doc examples, a pre-review self-check script) as the surface grows.
- **ROLLBACK**: The invariant tests prove flaky or low-value and are removed.
