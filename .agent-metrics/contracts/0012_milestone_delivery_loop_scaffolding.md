# Change Contract: 0012 - Milestone delivery loop scaffolding

- **ID**: `0012_milestone_delivery_loop_scaffolding`
- **Issue**: Scaffold a milestone-delivery loop harness (planner/implementor/reviewer/approver + supervisor loop)
- **Component**: Contributor process / harness docs (AGENTS.md, docs/agents/, docs/workflows/, platform stubs)
- **Created**: 2026-07-25
- **Status**: Proposed

## Observed Failure Evidence

This repo had no documented process for driving a GitHub milestone's issues
through to merged PRs with an agent in the loop, and no role separation
between planning, implementing, and reviewing work — a single undifferentiated
agent doing all of it tends to rubber-stamp its own work and lose track of
how many review rounds an issue has burned.

## Inferred Root Cause

The repo's harness docs (AGENTS.md, docs/review-checklist.md) cover
conventions for a human or single agent making one change, but never
specified a repeatable, role-separated delivery loop, or where such a loop's
definition should live so any agent tool (not just one platform) can follow
it.

## Proposed Change

Add a platform-neutral contributor conventions extension (testing standard,
complexity budget, docs-in-the-same-commit rule, delivery rules) plus four
narrow read-mostly role specs and a supervisor loop spec, all living under
`docs/` as the canonical source. Wire them into Claude Code with thin
`.claude/agents/` and `.claude/skills/` stubs, and add minimal cross-platform
pointer files (`CLAUDE.md`, `.cursor/rules/agents.mdc`,
`.github/copilot-instructions.md`) so other agent tooling can discover the
same conventions without duplicating them. Scaffolding only — no milestone is
actually driven by this change.

## Affected Component

- Contributor conventions: [AGENTS.md](../../AGENTS.md)
- Role specs: [docs/agents/](../../docs/agents/)
- Loop spec: [docs/workflows/milestone-delivery.md](../../docs/workflows/milestone-delivery.md)
- Claude Code wiring: `.claude/agents/`, `.claude/skills/milestone-delivery/`
- Cross-platform pointers: `CLAUDE.md`, `.cursor/rules/agents.mdc`, `.github/copilot-instructions.md`
- Changelog: [CHANGELOG.md](../../CHANGELOG.md)

## Predicted Fixes

- A future milestone run has a documented, role-separated loop to follow
  instead of one undifferentiated agent doing everything.
- Review-round counts and recurring bug-class escalation are explicit loop
  behavior, not something left to vibes.
- The same conventions are discoverable natively from Claude Code, Cursor,
  Codex, and Copilot without duplicating the content per platform.

## Regression Risks

- Docs-only change with no source/test edits; risk is limited to conventions
  drifting from what the loop is actually supposed to do if the canonical
  docs and the platform stubs fall out of sync.
- If a platform stub restates rather than defers to the canonical docs, the
  two could diverge over time.

## Verification Plan

1. Run `.venv/bin/python scripts/review.py` (`black --check`, `ruff check`,
   `pytest`) to confirm the docs-only change didn't break anything
   mechanizable.
2. Manually confirm every stub file defers to its canonical `docs/` source
   rather than restating it.
3. Manually confirm AGENTS.md's new sections stay consistent with the
   existing pyproject.toml complexity ceiling and CHANGELOG conventions.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: The doc/role/loop scaffolding is reviewed and judged usable as
  written, with no restructuring needed before it's used to actually drive a
  milestone.
- **IMPROVE**: The scaffolding is usable but needs adjustment (e.g. role
  boundaries, round caps, or escalation triggers) once exercised against a
  real milestone.
- **ROLLBACK**: The loop as specified doesn't hold up in practice (e.g. the
  thinness constraint proves unworkable, or the round-cap/escalation design
  doesn't actually catch runaway review cycles).

## Settlement

- **Settled**: 2026-07-25
- **Verdict**: KEEP

### Evidence

Added docs/agents/{planner,implementor,reviewer,approver}.md, docs/workflows/milestone-delivery.md, AGENTS.md sections (Testing Standard, Complexity & Quality Budget, Docs Updated in the Same Commit, Delivery Rules), .claude/agents/*.md and .claude/skills/milestone-delivery/SKILL.md wiring, and minimal cross-platform pointers (CLAUDE.md, .cursor/rules/agents.mdc, .github/copilot-instructions.md). All stubs defer to the canonical docs rather than restating them. .venv/bin/python scripts/review.py passed (black, ruff, pytest: 96 passed). Presented for human review before driving any real milestone, per the task's explicit scaffolding-only scope.
