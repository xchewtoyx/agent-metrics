# Change Contract: 0010 - Audit Command Implementation

- **ID**: `0010_audit_command`
- **Issue**: audit milestone
- **Component**: CLI / contracts
- **Created**: 2026-07-22
- **Status**: Proposed

## Observed Failure Evidence

`agent-metrics audit` is still a skeleton command, while the README describes it
as the command that should make missing contract and settlement practice visible.
Users cannot yet get a deterministic count of existing contract evidence or the
number of contracts that have been settled.

## Inferred Root Cause

The project has contract file naming and settlement conventions, but no reusable
library function that scans `.agent-metrics/contracts/*.md` and summarizes those
plain files for CI or local review.

## Proposed Change

Add a small file-based audit function to the contract module and wire
`agent-metrics audit` to print deterministic JSON. The first pass should audit
only markdown contract files under `.agent-metrics/contracts/`, ignore malformed
markdown that does not match the contract filename convention, and report the
limitation explicitly.

## Affected Component

- CLI entrypoint: [cli.py](../../src/agent_metrics/cli.py)
- Contract library module: [contracts.py](../../src/agent_metrics/contracts.py)
- Public package gateway: [__init__.py](../../src/agent_metrics/__init__.py)
- Tests: [test_cli.py](../../tests/test_cli.py), [test_contracts.py](../../tests/test_contracts.py)
- User docs: [README.md](../../README.md)

## Predicted Fixes

- `agent-metrics audit` reports contract counts and settled counts as stable JSON.
- Missing contract directories produce an explicit zero-count report rather than
  a crash.
- Malformed/non-contract markdown is counted separately enough to avoid hiding
  stray files.

## Regression Risks

- The command could imply complete git-change coverage when it only audits
  contract files.
- Counting settlement sections by heading could miss future alternate settlement
  formats.
- Publishing too much detail in the JSON shape could make the first API harder
  to evolve.

## Verification Plan

1. Add library tests for complete, missing, unsettled, and malformed/non-contract
   markdown states.
2. Add CLI tests for deterministic JSON and directory selection.
3. Run the narrow contract/CLI tests and the project review script if feasible.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: `agent-metrics audit` returns stable JSON counts for contract files,
  settled contracts, unsettled contracts, and ignored malformed markdown, and
  relevant tests pass.
- **IMPROVE**: Audit works, but needs richer details or git-based correlation in
  a later milestone.
- **ROLLBACK**: Audit crashes on ordinary missing state, miscounts settled
  contracts, or claims to cover all git changes.

## Settlement

- **Settled**: 2026-07-22
- **Verdict**: KEEP

### Evidence

Implemented file-based audit JSON, covered complete/missing/unsettled/malformed states, and passed .venv/bin/pytest tests/test_contracts.py tests/test_cli.py plus .venv/bin/python scripts/review.py.
