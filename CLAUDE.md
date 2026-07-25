# Claude Code

This project's contributor conventions live in [AGENTS.md](AGENTS.md) — read
that first, in full, before making changes.

For the milestone-delivery loop specifically: the operating spec is
[docs/workflows/milestone-delivery.md](docs/workflows/milestone-delivery.md),
run via the `milestone-delivery` skill (`.claude/skills/milestone-delivery/`),
which dispatches the four roles defined under
[docs/agents/](docs/agents/) (`planner`, `implementor`, `reviewer`,
`approver`; wired in as Claude Code subagents under `.claude/agents/`).

This file exists only to point Claude Code at those documents — it does not
duplicate them. Update the canonical files under `docs/`, not this one.
