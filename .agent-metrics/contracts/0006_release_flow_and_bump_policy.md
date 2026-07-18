# Change Contract: 0006 - Release Flow and Dual Version Bump Policy

- **ID**: `0006_release_flow_and_bump_policy`
- **Issue**: n/a (proactive infrastructure; follow-on from #3/#16 review)
- **Component**: Release / Docs / CI
- **Created**: 2026-07-18
- **Status**: Proposed

## Observed Failure Evidence

Review of the schema work surfaced two gaps:

- **No bump policy.** `schema_version` and `tool_version` evolve at different
  rates, but there was no written policy for when to bump either, nor a stated
  consumer-compatibility contract. The project was already relying on an
  unwritten "additive optional fields don't bump the schema" rule (for example
  `correlation_id` was added to `v1`).
- **No release flow.** `tool_version` now resolves from installed distribution
  metadata, but there was no documented or automated way to actually cut a
  release, so the version would never advance and there was no install path.

## Inferred Root Cause

The package began as a skeleton with a hard-coded version and no distribution
story. Versioning conventions and release automation were deferred.

## Proposed Change

Adopt the sibling `okf-core` release model (self-hosted PEP 503 index on GitHub
Pages, built from GitHub Release assets) and document both bump policies:

1. **Schema policy** in `docs/schemas.md`: per-record-type major versioning,
   bump on breaking shape/dedupe changes, no bump for additive optional fields,
   and an explicit consumer-compatibility contract (ignore unknown fields,
   tolerate missing optionals).
2. **Tool policy + release flow** in `docs/releasing.md`: SemVer for the package,
   the independence of `schema_version` and `tool_version`, and the step-by-step
   tag → GitHub Release → publish process.
3. **Automation**: `.github/workflows/publish.yml` (build, upload assets,
   generate index, deploy `gh-pages`) and `.github/scripts/gen_index.py` (PEP 503
   index over all published releases, with accumulated SHA-256 hashes).
4. Install instructions in `README.md` and an index pointer in `AGENTS.md`.

## Affected Component

- `.github/workflows/publish.yml`, `.github/scripts/gen_index.py`: automation.
- `docs/releasing.md`, `docs/schemas.md`: policies and flow.
- `README.md`, `AGENTS.md`: install path and doc index.

## Predicted Fixes

- A contributor can cut a release deterministically and consumers can `pip install`
  from the self-hosted index.
- `schema_version` and `tool_version` can advance independently with clear,
  documented rules, and consumers have a stated compatibility contract.

## Regression Risks

- **Pages/branch setup.** The index requires GitHub Pages served from `gh-pages`;
  documented as one-time setup. The first publish run creates the branch.
- **Index script drift.** `gen_index.py` is a workflow script outside the tested
  package (excluded from coverage). Its pure logic was smoke-tested; network
  paths rely on the GitHub API contract, mirroring the proven `okf-core` script.

## Verification Plan

1. **Checks**: `black`, `ruff` (the script is linted by `ruff check .`), and
   `pytest` pass at 100% coverage.
2. **Smoke test**: exercise `gen_index.py` asset detection, version sorting, and
   PEP 503 HTML generation locally without network.
3. **Docs**: cross-links between `releasing.md` and `schemas.md` resolve.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: Policies are documented and consistent, the workflow builds and
  publishes on release, the index installs, and all checks pass.
- **IMPROVE**: The flow works but needs refinement (e.g. release notes
  automation, version-bump tooling) once used for a real release.
- **ROLLBACK**: Self-hosted Pages distribution proves unworkable and a different
  distribution channel is needed.
