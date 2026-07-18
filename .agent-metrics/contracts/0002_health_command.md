# Change Contract: 0002 - Implement agent-metrics health --append (Metric-Agnostic)

- **ID**: `0002_health_command`
- **Issue**: [issue #2](https://github.com/xchewtoyx/agent-metrics/issues/2)
- **Component**: CLI / Health Command
- **Created**: 2026-07-18
- **Status**: Proposed

## Observed Failure Evidence

Currently, running `agent-metrics health` fails with:
`agent-metrics health` is a project skeleton command and is not implemented yet.

Without this command, developers and CI cannot establish baseline structural or codebase health metrics, leading to untracked quality degradation.

## Inferred Root Cause

The `health` command has not been implemented in [cli.py](../../src/agent_metrics/cli.py).

## Proposed Change

Implement the `health` command in [cli.py](../../src/agent_metrics/cli.py) to act as a generic metrics recorder and git envelope wrapper:
1. Accept input metrics via command line options:
   - `--metric KEY=VALUE` (multiple allowed, where value is cast to float/int if possible, otherwise string).
   - `--input-file PATH` (or `-` for stdin) to parse a JSON object of metrics.
2. Resolve repository git metadata:
   - HEAD commit SHA.
   - Origin remote URL.
   - Worktree dirty status.
3. Construct a standard JSON envelope:
   - `timestamp` (ISO 8601 UTC format).
   - `commit` (commit SHA, or null if not in git).
   - `remote_url` (remote origin URL, or null if not in git).
   - `dirty` (boolean).
   - `durable` (boolean, false if the worktree is dirty or not in git).
   - `tool_version` (version of agent-metrics).
   - `metrics` (dictionary containing the parsed input metrics).
4. Append this JSON object as a single line to `.agent-metrics/health.jsonl` (creating the parent directory if it does not exist).

## Affected Component

- [cli.py](../../src/agent_metrics/cli.py): CLI option and argument handling.
- `src/agent_metrics/health.py`: New module for git metadata resolution, input parsing, and JSONL appending.

## Predicted Fixes

- Running `agent-metrics health --append --metric tests=8 --metric failures=0` records the metrics wrapped in the git envelope inside `.agent-metrics/health.jsonl`.
- Running `echo '{"tests":8,"failures":0}' | agent-metrics health --append --input-file -` successfully parses and logs the metrics.
- Runs in dirty worktrees correctly set `durable` to `false`.

## Regression Risks

- **Non-Git Environments**: If the command is run outside of a git repository, it could crash. We must handle this by falling back gracefully (setting `commit` and `remote_url` to null, `dirty` to true, and `durable` to false) instead of raising an error.
- **Malformed Input**: If the user provides malformed JSON or invalid key-value arguments, it should display a clear user-facing error message and exit with a non-zero code.

## Verification Plan

1. **Unit Tests**:
   - Test git metadata extraction (clean, dirty, non-git directories) with mocked subprocess runs.
   - Test metrics input parsing (handling float/int/string conversion, handling `--metric` parsing).
   - Test JSON/stdin parsing (handling valid and invalid JSON).
   - Test CLI command invocation and argument combinations.
2. **Integration Tests**:
   - Run the full command on a mock workspace and assert that the generated `.agent-metrics/health.jsonl` contains the expected fields.
3. **Checks**:
   - Run `black`, `ruff`, and `pytest` to verify 100% code coverage.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: The command compiles, runs, writes correct structured envelopes to `.agent-metrics/health.jsonl`, handles non-git environments gracefully, and retains 100% test coverage.
- **IMPROVE**: The command works, but handling key-value casting or stdin reading is clunky, requiring CLI argument refinement.
- **ROLLBACK**: The generic approach is rejected or fails to represent OKF bundles cleanly, requiring a different design.
