---
name: milestone-delivery
description: Supervises a GitHub milestone through to completion, one issue at a time, via plan -> implement -> review -> approve -> PR -> human merge. Use when the user asks to run, drive, or continue the milestone delivery loop for a named milestone.
---

You are the supervisor for this repository's milestone-delivery loop.

Before doing anything else, read
`docs/workflows/milestone-delivery.md` in full — it is the canonical,
platform-neutral operating spec (the loop, the round caps, the escalation
rules, the batching rule, the polling-backoff rule). This file only wires
that spec into Claude Code; it does not restate it, and the spec wins if
anything here ever seems to conflict with it.

## How to run the loop here

- Take the target milestone (name or number) as an explicit argument. If
  none was given, ask for one — never assume or reuse a milestone from a
  previous run.
- Dispatch the four roles with the `Agent` tool, using the subagent types
  defined in `.claude/agents/planner.md`, `.claude/agents/implementor.md`,
  `.claude/agents/reviewer.md`, and `.claude/agents/approver.md`. Each of
  those, in turn, defers to its canonical spec under `docs/agents/`.
- Use the GitHub tools available in this session to query the milestone's
  open issues (fresh, every iteration — never cache the list), to open the
  PR, and, if available, to subscribe to PR activity instead of polling for
  merge state.
- Stay thin yourself: consume only the structured summaries each dispatched
  agent returns. Never read a full diff, PR thread, or issue body directly
  in this skill's own context — that's what `planner`/`reviewer`/`approver`
  are for.
- Surface the per-issue status line (`#N <title> — stage: review, round
  3/5`) on every iteration boundary and on every escalation, per
  `docs/workflows/milestone-delivery.md`.
- **Do not start driving a milestone unattended on first use.** Confirm the
  target milestone and get explicit go-ahead before opening the first PR of
  a run, unless the user has already made clear this is a standing,
  unattended job.
