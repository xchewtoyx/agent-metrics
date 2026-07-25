# Change Contract: 0009 - Settle Command Implementation

- **ID**: `0009_settle_command`
- **Issue**: settle milestone
- **Component**: CLI / contracts
- **Created**: 2026-07-22
- **Status**: Proposed

## Observed Failure Evidence

`agent-metrics settle` is currently an honest skeleton command. Contracts can be
scaffolded, but there is no project-owned way to record the eventual outcome and
verdict, so the documented contract loop still ends manually.

## Inferred Root Cause

The contract module only covers prediction scaffolding. It has no append-only
settlement operation, verdict validation, or CLI wrapper that can reject missing,
invalid, or already-settled contracts clearly.

## Proposed Change

Add a focused settlement function to the existing contracts module and wire a
minimal non-interactive CLI around it. The command should identify a contract by
path or contract id, require a validated verdict and evidence string, preserve
the original contract body, and append a clearly named settlement section once.

## Affected Component

- CLI entrypoint: [cli.py](../../src/agent_metrics/cli.py)
- Contract library module: [contracts.py](../../src/agent_metrics/contracts.py)
- Public package gateway: [__init__.py](../../src/agent_metrics/__init__.py)
- Tests: [test_cli.py](../../tests/test_cli.py), [test_contracts.py](../../tests/test_contracts.py)

## Predicted Fixes

- Users can settle a contract with `KEEP`, `IMPROVE`, or `ROLLBACK` evidence.
- Repeat settlement is rejected by default instead of silently overwriting prior
  evidence.
- Missing contracts and invalid verdicts fail through custom project exceptions.

## Regression Risks

- Contract id resolution could pick the wrong file if it accepts ambiguous input.
- Appending settlement text could disturb the original prediction body.
- The first CLI could overfit to future needs instead of staying minimal.

## Verification Plan

1. Add library tests for success, missing contract, invalid verdict, and repeat
   settlement.
2. Add CLI tests for the non-interactive command and user-facing failures.
3. Run the narrow contract/CLI tests and the project review script if feasible.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: `agent-metrics settle` appends exactly one settlement section,
  validates verdicts, preserves original contract text, and relevant tests pass.
- **IMPROVE**: Settlement works, but evidence input needs richer file/stdin
  support or optional settlement metadata.
- **ROLLBACK**: Settlement overwrites prediction content, accepts ambiguous
  verdicts, or permits repeated settlement without an explicit future override.

## Settlement

- **Settled**: 2026-07-22
- **Verdict**: KEEP

### Evidence

Implemented append-only settlement, covered success/missing-contract/invalid-verdict/repeat-settlement cases, and passed .venv/bin/pytest tests/test_contracts.py tests/test_cli.py plus .venv/bin/python scripts/review.py.
