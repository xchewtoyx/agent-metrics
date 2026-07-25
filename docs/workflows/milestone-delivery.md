# Milestone Delivery Loop

Operating spec for the supervisor that drives one GitHub milestone's open
issues to merged PRs, one issue at a time, using the four narrow roles in
[docs/agents/](../agents/): `planner`, `implementor`, `reviewer`, `approver`.

Any platform-specific skill/workflow stub (e.g. `.claude/skills/`) must defer
to this document rather than re-describing the loop. This file is the single
source of truth; keep it in sync when the loop's behavior changes.

## Input

A milestone identifier (name or number). **Never hard-code or cache a
worklist.** Every iteration re-queries the tracker for the milestone's
currently-open issues from scratch. If the milestone doesn't resolve to an
existing GitHub milestone, stop and ask — don't guess or silently fall back
to a label or issue list.

**Tooling note (GitHub MCP):** a generic issue-listing call can silently omit
the `milestone` field even when every issue has one — it did on this repo's
first pass. Confirm with a call that's known to surface `milestone` (e.g. a
search scoped with `milestone:"<title>"`, or reading one issue directly)
before concluding a milestone has no issues or doesn't exist.

## Thinness constraint

The supervisor is thin: it dispatches the four roles and reads only their
short structured summaries. It never reads a full diff, a full issue thread,
or a full PR review comment itself — if you find yourself about to `Read` a
diff or fetch full issue body text directly in the supervisor, that's a bug
in the loop; dispatch `planner`/`reviewer`/`approver` instead and consume
their summary.

## Per-issue state

Track, for as long as an issue is in flight, and surface on every progress
report:

- issue number and title
- current stage (plan / implement / review / approve / pr-open /
  awaiting-merge)
- review round count, out of the cap (e.g. `review 3/5`)
- approve round count, out of the cap (e.g. `approve 1/5`)

Report format: `#N <title> — stage: review, round 3/5`.

An issue sitting at round 4 or 5 must be visible in the very next progress
report, not discovered later from a cost or context overrun.

## Loop (one issue, end to end)

1. **Query.** Re-fetch the milestone's open issues from the tracker (e.g.
   `search_issues` with `milestone:"<title>" is:open`, not a generic
   unfiltered issue list — see the tooling note above). If none remain, the
   milestone is done — report and stop.
2. **Select.** Pick exactly one issue (lowest number, or the tracker's
   default order). Work it end-to-end before touching another.
3. **Branch.** Ensure a fresh branch exists for this issue
   (`issue-<N>-<slug>`, cut from the latest `main`). Never reuse a branch
   across issues, never force-push it.
4. **Plan.** Dispatch `planner` with the issue number. If it reports hard
   blockers (an unresolved dependency issue still open, or an unanswerable
   open question), escalate to the human immediately and move on to the
   next issue this iteration — don't spin on a blocked issue.
5. **Implement.** Dispatch `implementor` with the plan's subtasks.
6. **Review loop** (cap: 5 rounds):
   - Dispatch `reviewer` against the current diff.
   - `approve` → go to the approve loop.
   - `request_changes` → batch the findings (see *Batching*, below) and
     dispatch `implementor` once with the batch. Increment the round
     counter.
   - **Escalate immediately, before the cap, if either:**
     - the reviewer's bug-class circuit breaker fires (it says "bug-class
       recurrence #2"), or
     - two consecutive rounds report the same bug category in the same
       function/module without converging.
     Escalation = message the human with the recurring pattern and a
     recommendation to consider a structural fix, then pause this issue
     pending their input rather than burning the remaining rounds on
     symptom-patching. The round cap is a backstop for the cases the
     circuit breaker doesn't catch — not the primary signal to zoom out.
   - If the cap is exhausted without approval, escalate with the round
     history (stage summaries, not diffs) and pause the issue.
7. **Approve loop** (cap: 5 rounds), same mechanics as the review loop:
   - Dispatch `approver`. Failing criteria go back to `implementor` as one
     batch. Round-tracked the same way.
   - Escalate before the cap if the same criterion fails for the same
     structural reason two rounds running; escalate at the cap otherwise.
8. **Open PR.** Title from the issue; body includes `Closes #N`; use the
   repo's PR template if one exists (none as of this writing — until one
   is added, use a Summary / Test plan shape consistent with
   `docs/review-checklist.md`'s gates). Base branch `main`, head the
   issue's branch.
9. **Wait for human merge — hard, unskippable gate.** No auto-merge, no
   self-merge, ever, regardless of how clean the approve loop was. Prefer
   an event-driven subscription to PR activity over polling. If you must
   poll, back off: start at a short interval, double it after each check
   that shows no state change, cap it at a ceiling (for example: start at
   1 minute, cap at 30 minutes) — never poll at a fixed interval
   indefinitely.
10. **On merge or close.** Discard all working detail held for this issue
    (plan, diff state, round history) — keep only the completed-issue line
    (final round counts, PR link, outcome) in the human-visible progress
    report. Return to step 1 and re-query the milestone from scratch; do
    not carry any cached worklist forward.

## Batching

When multiple findings land close together on an open PR — several review
comments in one pass, or an automated reviewer re-triggering on every push —
wait a beat and collect them into a single `implementor` dispatch rather
than dispatching once per finding. One-at-a-time fix rounds are measurably
more expensive than a batched round covering the same findings.

## Escalation

Escalating means messaging the human directly with: the issue number, the
current round counts, the specific recurring pattern or blocker, and a
recommendation. It is not a GitHub comment aimed at nobody in particular.
After escalating, pause that issue and wait for direction before spending
further rounds on it; continue working other issues in the meantime if any
are in flight.
