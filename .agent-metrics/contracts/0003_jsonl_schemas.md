# Change Contract: 0003 - Define JSONL Schemas and Provenance Envelope

- **ID**: `0003_jsonl_schemas`
- **Issue**: [issue #3](https://github.com/xchewtoyx/agent-metrics/issues/3)
- **Component**: Library / Provenance & Schemas
- **Created**: 2026-07-18
- **Status**: Proposed

## Observed Failure Evidence

The `health` command records a JSON envelope, but the envelope is ad-hoc and
insufficient for cross-checkout deduplication:

- Records carry no `schema_version`, so consumers cannot evolve the record shape
  safely or tell record kinds apart.
- The envelope omits `branch`, `host`, and a `bundle` identifier, so the same
  bundle measured at the same commit on different hosts or branches cannot be
  reconciled.
- Durability was reduced to a single `durable` boolean (`not dirty`), which does
  not distinguish authoritative CI-on-merge evidence from advisory local runs.
- There is no defined schema for effectiveness (A/B replay) records, and no
  documented example JSONL for any record type.

## Inferred Root Cause

The provenance envelope was introduced incrementally alongside the `health`
command without a versioned, documented schema shared across record types. There
was no single module owning identity, context, durability, and deduplication.

## Proposed Change

1. Add a `provenance` module defining:
   - Versioned schema identifiers for structural health and effectiveness records.
   - A `build_provenance` envelope carrying `schema_version`, `remote_url`,
     `commit`, `branch`, `dirty`, `bundle`, `host`, `environment`, `durability`,
     `timestamp`, and `tool_version`.
   - Git identity resolution (now including `branch`), host resolution, CI
     detection, durability classification, and reproducible timestamps.
   - `structural_health_dedupe_key` `(repo, bundle, commit, schema_version)` and
     `effectiveness_dedupe_key` (adding model, harness version, task set, run
     index, and experiment arms), plus a `build_effectiveness_envelope` builder.
2. Refactor `health.py` so structural health records are built from the shared
   envelope, and add a `--bundle` option to the `health` command.
3. Export the new schema API from the package root.
4. Document the schemas and example JSONL records in `docs/schemas.md`.

## Affected Component

- `src/agent_metrics/provenance.py`: new module.
- [health.py](../../src/agent_metrics/health.py): builds records via the envelope.
- [cli.py](../../src/agent_metrics/cli.py): `--bundle` option.
- [__init__.py](../../src/agent_metrics/__init__.py): public API exports.
- `docs/schemas.md`: schema and example documentation.

## Predicted Fixes

- Every record includes `schema_version`, remote URL, commit, branch, dirty flag,
  bundle, host, timestamp, and tool version.
- Structural health records dedupe on `(repo, bundle, commit, schema_version)`,
  ignoring branch and host context.
- Effectiveness records additionally include model, harness version, task set,
  run index, and experiment arms.
- Durable CI-on-merge records are distinguishable from advisory local runs.
- Example JSONL records are documented in the repository.

## Regression Risks

- **Schema Break**: The health record shape changes (new fields, `durable`
  boolean removed). Downstream consumers of the old shape must adapt; the
  `schema_version` field makes this explicit going forward.
- **CI Detection Heuristic**: Durability relies on the `CI` environment flag. A
  misconfigured environment could misclassify a record, though it fails safe to
  `advisory`.

## Verification Plan

1. **Unit Tests**: Cover git metadata (with branch), host and CI detection,
   durability classification, timestamp handling, envelope assembly, both
   builders, and both dedupe keys, including the cross-host/branch dedupe case.
2. **Integration Tests**: Assert the `health` CLI records the bundle and schema
   fields.
3. **Checks**: `black`, `ruff`, and `pytest` pass with 100% coverage.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: The schemas are defined, documented with example JSONL, deduplicate
  by commit-keyed identity, distinguish durable from advisory records, and all
  checks pass at 100% coverage.
- **IMPROVE**: The schemas work but field names, the durability heuristic, or the
  effectiveness shape need refinement once `roll`/`audit` consume them.
- **ROLLBACK**: The envelope proves unable to represent bundles or effectiveness
  records cleanly, requiring a different identity model.
