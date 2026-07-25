# Change Contract: 0011 - CI Health Snapshot Integration

- **ID**: `0011_ci_health_snapshot`
- **Issue**: CI health snapshots milestone
- **Component**: GitHub Actions / health snapshots
- **Created**: 2026-07-22
- **Status**: Proposed

## Observed Failure Evidence

`agent-metrics health --append` exists, but this repository does not yet dogfood
it in CI. The README says session-end or CI checks should run health snapshots
in first adopter repos, so successful test runs currently leave no durable
plain-file health evidence attached to the CI run.

## Inferred Root Cause

The Stage One CLI landed before the GitHub Actions integration. The existing
test workflow installs the package and runs cheap checks, but has no post-test
step that calls the installed CLI or preserves `.agent-metrics/health.jsonl`
outside the worktree.

## Proposed Change

Extend the existing GitHub Actions test workflow with a small health snapshot
step after `pytest`. Use the installed `agent-metrics` console script with
`health --append` and deterministic explicit metrics, then upload
`.agent-metrics/health.jsonl` as an artifact. Document the artifact behavior and
add a lightweight workflow-shape test.

## Affected Component

- Test workflow: [tests.yml](../../.github/workflows/tests.yml)
- Workflow verification: [test_workflows.py](../../tests/test_workflows.py)
- User docs: [README.md](../../README.md)
- Changelog: [CHANGELOG.md](../../CHANGELOG.md)

## Predicted Fixes

- CI produces an inspectable structural health JSONL record without committing
  generated records.
- The snapshot is service-free and uses the same installed CLI users run
  locally.
- The metric set stays deterministic and cheap for this repo's Stage One needs.

## Regression Risks

- Uploading artifacts could fail if the health step writes to the wrong path.
- Static metrics could be mistaken for full command-derived telemetry.
- A workflow assertion could become brittle if it checks formatting instead of
  the intended step behavior.

## Verification Plan

1. Add a static workflow test that asserts `agent-metrics health --append` is
   present and the health JSONL path is uploaded as an artifact.
2. Run the workflow test and narrow CLI/health tests.
3. Run `.venv/bin/python scripts/review.py` if feasible.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: The workflow records `.agent-metrics/health.jsonl` with the
  installed CLI after tests, uploads it as a GitHub Actions artifact, docs note
  the static metric limitation, and relevant checks pass.
- **IMPROVE**: CI snapshot works, but the metric set should later become richer
  or command-derived.
- **ROLLBACK**: CI does not produce an inspectable JSONL artifact or the new
  workflow step makes ordinary test runs fail.

## Settlement

- **Settled**: 2026-07-22
- **Verdict**: KEEP

### Evidence

Implemented CI health snapshot in the existing test workflow using the installed agent-metrics health --append command, uploaded .agent-metrics/health.jsonl as the agent-metrics-health artifact, documented the static metric limitation, added a workflow-shape test, passed .venv/bin/pytest tests/test_workflows.py tests/test_health.py tests/test_cli.py, and passed .venv/bin/python scripts/review.py.
