# Change Contract: 0008 - Contract Command Implementation

- **ID**: `0008_contract_command`
- **Issue**: contract milestone
- **Component**: CLI / contracts
- **Created**: 2026-07-22
- **Status**: Proposed

## Observed Failure Evidence

`agent-metrics contract` is currently a skeleton command that fails with "not
implemented yet". Developers following the golden path must hand-write contract
files, including choosing the next numeric prefix and preserving the expected
sections, which is easy to do inconsistently.

## Inferred Root Cause

The project has documented contract conventions, but no reusable library code or
thin CLI wrapper that turns a title/slug into a deterministic markdown scaffold.
Filename allocation and collision handling are implicit manual steps.

## Proposed Change

Add focused contract-scaffolding library code and wire `agent-metrics contract`
to it. The minimal non-interactive path should accept a title or slug, create a
markdown file under `.agent-metrics/contracts/`, fill the standard prediction
sections with placeholders, and fail clearly when the requested deterministic
filename would collide or the slug is invalid.

## Affected Component

- CLI entrypoint: [cli.py](../../src/agent_metrics/cli.py)
- Contract library module: [contracts.py](../../src/agent_metrics/contracts.py)
- Public package gateway: [__init__.py](../../src/agent_metrics/__init__.py)
- Tests: [test_cli.py](../../tests/test_cli.py), [test_contracts.py](../../tests/test_contracts.py)

## Predicted Fixes

- Developers can run a single non-interactive command to scaffold a contract.
- Generated contract names are deterministic and easy to audit.
- Collisions and invalid names fail through project-level custom exceptions
  rather than overwriting evidence.

## Regression Risks

- The command could guess an unexpected numeric prefix if existing files use
  unusual names.
- Slug validation that is too strict could reject reasonable titles.
- Publishing too many helpers through `__all__` could widen the API surface more
  than needed.

## Verification Plan

1. Add library tests for happy path scaffolding, slug derivation, invalid slug
   rejection, and collision rejection.
2. Add CLI tests proving the command delegates cleanly and prints the created
   path.
3. Run the narrow contract/CLI tests and the project review script if feasible.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: `agent-metrics contract` creates a deterministic markdown scaffold,
  rejects invalid/colliding names clearly, and all relevant tests pass.
- **IMPROVE**: The command works, but users need richer metadata options or more
  flexible templates.
- **ROLLBACK**: The command overwrites evidence, creates ambiguous filenames, or
  makes contract creation less predictable than the manual workflow.
