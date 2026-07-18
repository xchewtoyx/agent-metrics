# agent-metrics

`agent-metrics` is a lightweight, serverless metrics toolkit for agent and knowledge repos.
Its first CLI is expected to be `ahekit`: a tiny helper that turns changes to an agent
harness or knowledge base into falsifiable, evidence-settled contracts.

The project exists because several sibling agent repos independently built the same
evaluation scaffolding: change contracts, A/B replays, outcome rubrics, and harness
experiment protocols. The scaffolding captured predictions, but rarely closed the loop
with measured outcomes. `agent-metrics` keeps that loop cheap enough to run and visible
enough to audit.

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

1. `ahekit health --append` records structural health as append-only JSONL.
2. `ahekit contract` scaffolds a one-file pre-change prediction.
3. `ahekit settle` records the outcome and verdict for a contract.
4. `ahekit audit` reports how many harness changes had contracts and settled outcomes.
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
hosts.

### Make Missing Evidence Visible

The anti-aspiration metric matters: if evaluation scaffolding changes are merged without
contracts or outcomes, `audit` should make that visible.

## Expected Commands

```text
ahekit health --append
ahekit contract
ahekit settle
ahekit audit
ahekit roll
```

These names are placeholders until implementation starts. The repository currently
contains planning material only.

## Source

This repository was initialized from the cross-project analysis pitch in:

`tasks/km-cross-project-analysis/08-tool-elevator-pitch.md`

from the `ado` worktree analyzed on 2026-07-18.
