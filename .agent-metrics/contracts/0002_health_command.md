# Change Contract: 0002 - Implement agent-metrics health --append

- **ID**: `0002_health_command`
- **Issue**: [issue #2](https://github.com/xchewtoyx/agent-metrics/issues/2)
- **Component**: CLI / Health Command
- **Created**: 2026-07-18
- **Status**: Proposed

## Observed Failure Evidence

Currently, there is no way to record structural health snapshots of a repository/bundle. Running `agent-metrics health` fails with:
`agent-metrics health` is a project skeleton command and is not implemented yet.

Without this command, developers and CI cannot establish baseline structural metrics or track progression over time, leading to silent degradation of markdown links, untracked orphans, and duplicates.

## Inferred Root Cause

The `health` command has not been implemented in [cli.py](../../src/agent_metrics/cli.py).

## Proposed Change

Implement the `health` command in [cli.py](../../src/agent_metrics/cli.py) to:
1. Traverse the specified directory (defaulting to `.`) to find markdown files.
2. Parse each file for frontmatter (YAML) and links (both standard Markdown links `[text](url)` and WikiLinks `[[target]]`).
3. Build a directed link graph to compute:
   - `concept_count`: Total number of markdown files.
   - `true_orphans`: Files with in-degree = 0 and out-degree = 0.
   - `seed_only_nodes`: Files with in-degree = 0 and out-degree > 0.
   - `broken_links`: Links referencing non-existent files in the bundle.
   - `median_degree` & `max_degree`: Computed over `in_degree + out_degree`.
   - `top_hubs`: Top 3-5 files by out-degree.
   - `duplicate_candidates`: Files with identical content hashes or identical titles in frontmatter.
   - `stale_provenance_count`: Files with a `commit` or `sha` frontmatter key that does not match the actual last git commit SHA that modified the file.
4. Extract git context for the repository (current HEAD commit SHA, remote origin URL, and dirty worktree status).
5. Append a single JSONL line containing these metrics, timestamp, tool version, and a `durable` flag (false if the worktree is dirty/advisory) to `.agent-metrics/health.jsonl`.

## Affected Component

- [cli.py](../../src/agent_metrics/cli.py): CLI option handling.
- New module `src/agent_metrics/health.py`: Health analysis logic.

## Predicted Fixes

- Running `agent-metrics health --append` generates a valid JSONL entry at `.agent-metrics/health.jsonl`.
- The outputs are deterministic for the same repository commit and tool version.
- Uncommitted edits will be correctly labeled as advisory (`durable: false`).

## Regression Risks

- **Git Dependency**: The tool relies on Git to retrieve commit and remote information. If run in a non-git directory or if Git is not installed, it could crash. We must handle this by falling back gracefully (e.g. setting `commit`, `remote_url` to null/empty and marking the run as advisory).
- **Performance**: Parsing large numbers of markdown files might be slow. We should use simple regex-based parsing instead of heavyweight AST parsers to keep it fast, and keep it dependency-free.
- **Parsing False Positives**: Code blocks containing markdown links or wiki links could be incorrectly parsed as active links. We should exclude code blocks (lines between triple backticks ` ``` `) from link scanning.

## Verification Plan

1. **Unit Tests**:
   - Test markdown link and WikiLink extraction logic, including section anchor scrubbing and extension handling.
   - Test degree calculations, true orphans, and seed-only node detection using mock files.
   - Test duplicate candidate detection (content hashes and frontmatter titles).
   - Test stale provenance detection using mock git commit SHAs.
   - Test CLI argument handling, checking error codes and formatting.
2. **Integration Tests**:
   - Run the health command on a mock repository with clean and dirty worktree states and verify the appended JSONL file.
3. **Checks**:
   - Run `black`, `ruff`, and `pytest` to ensure 100% test coverage and code compliance.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: The command runs successfully, writes correct metrics to `.agent-metrics/health.jsonl`, handles edge cases (like non-git repos or code blocks) without crashing, and maintains 100% test coverage.
- **IMPROVE**: The command functions but is too slow on larger repositories or misses complex link structures, requiring parser refinements.
- **ROLLBACK**: The analysis is unreliable, generates inaccurate graph metrics, or introduces significant complexity, suggesting a different library-based parsing approach.
