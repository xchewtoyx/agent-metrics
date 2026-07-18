# Change Contract: 0001 - Initial agent-metrics CLI Implementation

- **ID**: `0001_initial_milestone`
- **Issue**: [issue #1](https://github.com/xchewtoyx/agent-metrics/issues/1)
- **Component**: CLI
- **Created**: 2026-07-18
- **Status**: Proposed

## Observed Failure Evidence

Currently, multiple sibling agent and knowledge base repositories independently implement duplicate, ad-hoc, and inconsistent evaluation and metrics gathering logic (e.g., A/B replays, outcome rubrics, validation code).
- Changes to agent harnesses or knowledge bundles are regularly committed without defining a testable prediction beforehand.
- There is no central, standardized, or low-overhead way to record whether harness or knowledge edits actually improve downstream agent performance.
- Evals and outcomes are rarely cross-referenced or audited with git commits/SHAs, making it difficult to trace code provenance and audit evaluation compliance.

## Inferred Root Cause

There is no lightweight, serverless metrics toolkit available that:
1. Records structural repo/bundle health dynamically.
2. Scaffolds a pre-change contract to force falsifiable predictions.
3. Records explicit outcomes and verdicts (KEEP, IMPROVE, ROLLBACK) for those changes.
4. Audits compliance at the commit level using plain files (JSONL and markdown).

Because of this lack of tooling, teams defaults to not writing/checking evaluation contracts, leading to unverified changes and potential regressions.

## Proposed Change

Design and implement the `agent-metrics` package structure and a CLI with five placeholder commands:
1. `health` (recording structural health snapshot as append-only JSONL to `.agent-metrics/health.jsonl`).
2. `contract` (scaffolding a pre-change markdown contract prediction).
3. `settle` (recording outcomes/verdicts).
4. `audit` (reporting how many harness changes had contracts and settled outcomes).
5. `roll` (aggregating metrics across repositories and commits).

This initial work lays the foundations of the toolkit by dogfooding the process using this very contract.

## Affected Component

- CLI entrypoint: [cli.py](file:///home/rgh/git/gh/xchewtoyx/agent-metrics/src/agent_metrics/cli.py)
- Package configuration: [pyproject.toml](file:///home/rgh/git/gh/xchewtoyx/agent-metrics/pyproject.toml)

## Predicted Fixes

- Developers can scaffold a contract immediately using `agent-metrics contract`.
- Un-evaluated changes are made visible to CI/auditors via `agent-metrics audit`.
- Metric outputs are cleanly structured and keyable by commit/remote URL to ensure provenance and prevent duplication.

## Regression Risks

- **Developer Friction**: The requirement to file and settle contracts adds manual overhead, which could lead to developer fatigue or bypassing.
- **Stale Evidence**: Contracts or outcome files may become out of sync with the repository state if the settlement workflow is not properly integrated into developer habits or CI.
- **Complexity**: If the command options or templates are too rigid or verbose, the toolkit becomes hard to maintain and adopt.

## Verification Plan

1. **Unit and Integration Tests**:
   - Implement tests covering command-line options, inputs, outputs, and validation.
   - Verify that invalid commands are correctly rejected with clear user-facing error messages.
2. **Linting and Formatting**:
   - Ensure the new CLI and utility code passes all ruff lint checks and black formatting tests cleanly.
   - Maintain 100% test coverage for all new implementation.
3. **Dogfooding**:
   - Use the `agent-metrics` tools to verify this contract and settle it.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: The CLI successfully compiles, installs, passes all checks (100% test coverage), and makes it simple to generate contracts and health logs. The developer experience is low friction.
- **IMPROVE**: The tool works, but feedback indicates that the CLI arguments or generated markdown templates require refactoring to reduce friction or add useful metadata.
- **ROLLBACK**: The manual overhead of creating and settling contracts causes developers to bypass the tool, or the implementation details are too complex/unreliable, requiring a rethink of the workflow.
