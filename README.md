# agent-metrics

`agent-metrics` is a lightweight, serverless metrics toolkit for agent and knowledge repos.
Its first CLI turns changes to an agent harness or knowledge base into falsifiable,
evidence-settled contracts.

The project exists because several sibling agent repos independently built the same
evaluation scaffolding: change contracts, A/B replays, outcome rubrics, and harness
experiment protocols. The scaffolding captured predictions, but rarely closed the loop
with measured outcomes. `agent-metrics` keeps that loop cheap enough to run and visible
enough to audit.

## Installation

`agent-metrics` is distributed as a self-hosted PEP 503 simple index on GitHub
Pages, not on PyPI:

```bash
pip install agent-metrics \
  --index-url https://xchewtoyx.github.io/agent-metrics/simple/ \
  --extra-index-url https://pypi.org/simple/
```

See [docs/releasing.md](docs/releasing.md) for the versioning policy and the
tag-and-release flow.

## Goals

- Record objective structural health snapshots for markdown and OKF-style knowledge
  bundles.
- Scaffold a change contract before load-bearing harness or knowledge edits.
- Settle each contract after the next run with evidence and a clear verdict:
  `KEEP`, `IMPROVE`, or `ROLLBACK`.
- Audit whether evaluation practice is actually happening: changes merged, contracts
  recorded, outcomes settled.
- Aggregate JSONL metrics across repositories, branches, hosts, and commits without
  requiring a service or database.

## Non-goals

- No hosted metrics platform.
- No central database in the first milestone.
- No eval-of-record for every task.
- No scheduled ceremony for expensive effectiveness evaluations.
- No task-outcome or LLM-judge logic inside `okf-core`.

## First Milestone

The first milestone is deliberately small:

1. `agent-metrics health --append` records structural health as append-only JSONL.
2. `agent-metrics contract "Title"` scaffolds a one-file pre-change prediction.
3. `agent-metrics settle` records the outcome and verdict for a contract.
4. `agent-metrics audit` reports how many harness changes had contracts and settled outcomes.
5. Session-end or CI checks run health snapshots in the first adopter repos.

The project should dogfood its own rule: building this toolkit is itself a harness
change, so the first implementation work should start with a contract.

## Design Principles

### Separate Cheap Health From Expensive Effectiveness

Structural health is mechanical: concept count, orphans, broken links, degree, duplicate
candidates, and stale provenance. It should run continuously.

Effectiveness is judgment-heavy: did a pack, lens, routing rule, guardrail, or schema
change actually improve agent outcomes? It should run only when a shared, load-bearing
surface changes.

### Use Plain Files First

Metrics are JSONL and markdown records that can be grepped, committed, merged, and
harvested later. Promote to SQLite or DuckDB only when volume demands it.

### Key Structural Metrics By Commit

Every record carries a provenance envelope keyed on the remote URL and commit SHA, not
the local checkout path. The same bundle at the same commit should dedupe cleanly across
hosts. The versioned record schemas, the provenance envelope, the durable/advisory
distinction, and example JSONL records are documented in
[docs/schemas.md](docs/schemas.md).

### Make Missing Evidence Visible

The anti-aspiration metric matters: if evaluation scaffolding changes are merged without
contracts or outcomes, `audit` should make that visible.

## Expected Commands

```text
agent-metrics health --append --metric concepts=128 .
agent-metrics contract "Measure harness drift"
agent-metrics settle 0001_measure_harness_drift --verdict KEEP --evidence "Checks passed."
agent-metrics audit
agent-metrics roll
```

`health` records metric-agnostic structural snapshots as JSON. With `--append`, it
also writes append-only JSONL under `.agent-metrics/health.jsonl`.

`contract` requires a title and writes the next deterministic markdown scaffold under
`.agent-metrics/contracts/`. `settle` appends a settlement section with a validated
`KEEP`, `IMPROVE`, or `ROLLBACK` verdict and rejects repeat settlements by default.
Later Stage One commands (`audit` and `roll`) are still honest stubs until their
milestones land.

## Development

Install the package with development tools:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Prefer a project-local virtual environment at `.venv/` when developing locally. The
path is ignored by Git.

Run the local checks:

```bash
black .
ruff check .
pytest
```

The test suite uses `pytest` with coverage enabled through `pyproject.toml`. Current
tests cover the implemented `health`, `contract`, and `settle` commands,
version/help output, clear failure for remaining unimplemented commands, and
rejection of unknown commands.

Formatting is handled by Black. Linting is handled by Ruff, including McCabe complexity
checks, so new implementation should stay simple before it gets broad.

## Development Philosophy

The aim is robust, efficient, minimal tooling. Prefer existing libraries and standard
Python tooling before adding custom machinery. Build behavior with tests first where
practical, and cover both positive and negative cases so failures are explicit rather
than surprising.

## Source

This repository was initialized from the cross-project analysis pitch in:

`tasks/km-cross-project-analysis/08-tool-elevator-pitch.md`

from the `ado` worktree analyzed on 2026-07-18.

## References

- [Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses](https://arxiv.org/abs/2604.25850)
- [Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
- [Estimating AI productivity gains from Claude conversations](https://www.anthropic.com/research/estimating-productivity-gains)
- [Anthropic Economic Index report: Economic primitives](https://www.anthropic.com/research/anthropic-economic-index-january-2026-report)
