# Change Contract: 0004 - Align JSONL Schemas with OpenTelemetry GenAI Conventions

- **ID**: `0004_otel_alignment`
- **Issue**: [issue #14](https://github.com/xchewtoyx/agent-metrics/issues/14)
- **Component**: Library / Provenance & Schemas
- **Created**: 2026-07-18
- **Status**: Proposed

## Observed Failure Evidence

Issues #11-#15 add a second wave of telemetry (wrapper blocks, workaround/evasion,
friction overhead) and ask that agent-metrics map cleanly onto OpenTelemetry
GenAI semantic conventions instead of becoming a parallel standard. The schema
defined in #3 is close but was not yet interoperable:

- Novel fields had no reserved namespace, risking collisions with future OTel
  attributes.
- There was no correlation id to reconstruct related records as a timeline, which
  every one of #12-#14 requires.
- There was no defined, tested mapping from our JSONL fields to OTLP attribute
  names, so "export OTLP later" was an unscoped rewrite rather than a solved path.

## Inferred Root Cause

The #3 schema was designed for durable local evidence first. Interoperability
with observability backends (Phoenix, MLflow, any OTLP consumer) was deferred and
had no connective tissue between the on-disk records and the OTel conventions.

## Proposed Change

Add early, low-cost alignment without coupling the durable on-disk schema to
in-flux specifications:

1. Reserve the `agent_metrics.*` namespace (`AGENT_METRICS_NAMESPACE`) for
   concepts with no stable OTel home.
2. Add an optional `correlation_id` envelope field (omitted when unset), plumbed
   through `build_provenance`, `build_effectiveness_envelope`,
   `create_health_envelope`, `capture_health`, and a `health --correlation-id`
   option; it maps to `gen_ai.conversation.id`.
3. Add `to_otel_attributes(record)` mapping records onto `vcs.*`, `gen_ai.*`,
   `host.*`, and `service.*` conventions, namespacing everything else, excluding
   `timestamp` and `metrics`, and omitting `None` values. Document the mapping in
   `docs/schemas.md`.

## Affected Component

- `src/agent_metrics/provenance.py`: namespace, mapping, correlation id, exporter.
- [health.py](../../src/agent_metrics/health.py) and
  [cli.py](../../src/agent_metrics/cli.py): correlation id plumbing.
- [__init__.py](../../src/agent_metrics/__init__.py): public API exports.
- `docs/schemas.md`: OpenTelemetry alignment section and mapping table.

## Predicted Fixes

- Records can be exported to OTLP attribute names via a single tested boundary.
- Novel and future fields stay collision-safe under `agent_metrics.*`.
- Related records (block, workaround, recovery) can share a `correlation_id`
  timeline, unblocking #11-#14 without a schema-version bump.

## Regression Risks

- **Spec Drift**: `vcs.*` is Release Candidate and `gen_ai.*` is still evolving.
  Mapping only at the export boundary contains the blast radius to
  `to_otel_attributes` and its tests.
- **Attribute Value Types**: Nested payloads are not valid OTel attributes; the
  helper excludes `metrics` and documents that callers flatten measurements into
  metric data points.

## Verification Plan

1. **Unit Tests**: Cover the known-convention mapping, namespaced novel fields,
   effectiveness coordinates, `None` omission, and optional `correlation_id`
   inclusion in the envelope and via the CLI.
2. **Checks**: `black`, `ruff`, and `pytest` pass with 100% coverage.

## Settle Criteria (Evidence for Verdict)

- **KEEP**: The mapping helper, reserved namespace, and correlation id are in
  place, documented, and tested at 100% coverage, and the on-disk schema stays
  decoupled from the in-flux OTel specs.
- **IMPROVE**: The mapping works but field choices need revision once the #11-#15
  event types and a real OTLP exporter consume it.
- **ROLLBACK**: Boundary mapping proves insufficient and the records must instead
  adopt OTel attribute names on disk, requiring a different approach.
