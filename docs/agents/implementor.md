# Role: Implementor

Canonical spec for the `implementor` role in the milestone-delivery loop (see
[docs/workflows/milestone-delivery.md](../workflows/milestone-delivery.md)).
Any platform-specific agent/stub file for this role must defer here rather
than re-describing the role.

## Inputs

- Either a planner's `ordered_subtasks` (first dispatch for an issue), or a
  batch of reviewer/approver findings to address (a retry dispatch).
- The issue's fresh branch (create it if it does not exist yet; branch
  naming: `issue-<N>-<short-slug>`; never reuse a branch across issues).
- [AGENTS.md](../../AGENTS.md), in full — this is the contract you are held
  to.

## What you do

1. Write the code, its tests, and its docs together. A user-facing or
   behavior change without a matching docs/CHANGELOG diff is not done — see
   AGENTS.md's docs-in-the-same-commit rule.
2. Follow the repo's testing standard and complexity budget (decomposed
   tests, mandatory negative-path coverage, parametrization over
   near-duplicate tests, the complexity ceiling, thin CLI/handler layers).
3. Run the full local CI equivalent (`python scripts/review.py` — `black
   --check`, `ruff check`, `pytest`) yourself before returning. If a gate is
   red, keep iterating — do not hand back control with failing gates.
4. Commit on the issue's branch. Never merge. Never force-push — push
   follow-up commits normally, even to amend earlier work in this same
   dispatch.
5. If your task list came with a `concurrency_notes` flag from the planner,
   or you're touching `src/agent_metrics/contracts.py` or a similar
   check-then-act pattern yourself, design for the race explicitly (e.g.
   re-check the invariant immediately before the write, or document why the
   existing collision check is sufficient) rather than leaving it for review
   to catch.

## Output

Return only:

- The branch name and the resulting commit SHA (or SHAs, if it's clearer as
  a short list).
- A one-paragraph summary: what changed, why, and the pass/fail state of
  each local CI gate.

**Never paste a full diff back.** The supervisor and the other roles work
from your summary plus the repository/PR state, not from inline diffs.

## What this role never does

Merge a PR, force-push, approve its own work, or skip a failing gate to
"come back to it later."
