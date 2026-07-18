# Change Contract: 0005 - Trim and Align the Public API Surface

- **ID**: `0005_api_surface_cleanup`
- **Issue**: n/a (proactive Boy Scout cleanup)
- **Component**: Library / Public API
- **Created**: 2026-07-18
- **Status**: Proposed

## Observed Failure Evidence

The package-level public API (`agent_metrics.__all__`) grew from ~9 names to 22
across the #3 and #14 work, and two smells emerged:

- **Naming asymmetry.** The three record builders drifted apart:
  `build_provenance`, `create_health_envelope`, and `build_effectiveness_envelope`
  used inconsistent verbs and suffixes, so the two record-type builders a
  consumer chooses between did not read as a pair.
- **Layering leak.** Low-level envelope mechanics — `get_host`,
  `detect_environment`, `classify_durability` — were exported despite having a
  single internal caller each (`build_provenance`) and no external consumer need.
  Together with the thin `create_health_envelope` wrapper, `dir(agent_metrics)`
  exposed four overlapping ways to make a record and four git/host/env helpers,
  obscuring the real entry points.

## Inferred Root Cause

The builders and helpers were added in separate passes without a final review of
the public gateway, so intermediate building blocks were published alongside the
high-level API instead of remaining internal implementation details.

## Proposed Change

Bring the surface back to its intended shape, per the AGENTS.md rule that
`__all__` is the strict gateway and internals stay out of it:

1. Rename `create_health_envelope` to `build_health_envelope` so the two
   record-type builders (`build_health_envelope`, `build_effectiveness_envelope`)
   are a consistent pair over the shared `build_provenance` base.
2. Remove `get_host`, `detect_environment`, and `classify_durability` from the
   package root. They remain in `agent_metrics.provenance` as internal building
   blocks used by `build_provenance` and covered by their own tests.

## Affected Component

- [health.py](../../src/agent_metrics/health.py): renamed builder.
- [__init__.py](../../src/agent_metrics/__init__.py): public exports.
- [tests/test_health.py](../../tests/test_health.py): updated references.
- `CHANGELOG.md`: recorded rename and trim.

## Predicted Fixes

- A consumer sees a coherent builder story: `build_provenance` (base),
  `build_health_envelope` and `build_effectiveness_envelope` (records), and
  `capture_health` (gather inputs, build, optionally append).
- The public API commits only to names external users need; internal mechanics
  can be refactored freely.

## Regression Risks

- **Breaking rename.** `create_health_envelope` and the three removed helpers are
  no longer importable from the package root. The project is pre-1.0 with no
  external consumers, so the cost is minimal now and rises later; this is the
  cheapest moment to correct it.

## Verification Plan

1. **Tests**: Update references and confirm `black`, `ruff`, and `pytest` pass at
   100% coverage.
2. **Manual**: Import the renamed builder and confirm the removed helpers are
   absent from `agent_metrics.__all__` but present in `agent_metrics.provenance`.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: The surface is smaller and internally consistent, all checks pass at
  100% coverage, and the removed helpers remain available internally.
- **IMPROVE**: The trim is right but further names (for example `parse_metric_value`)
  warrant review once downstream consumers appear.
- **ROLLBACK**: A removed helper turns out to be needed publicly, requiring it to
  be re-exported.
