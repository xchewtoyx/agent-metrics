# JSONL Schemas and Provenance Envelope

`agent-metrics` records are newline-delimited JSON (JSONL): one self-describing
record per line, grep-able, committable, and mergeable without a service or
database. Every record carries a **provenance envelope** so that the same bundle
measured at the same commit deduplicates cleanly across local checkouts, hosts,
branches, and CI runs.

Records are versioned. The `schema_version` field names the record shape so
consumers can evolve their handling as schemas change. See the bump and
compatibility policy below.

## Schema versioning and compatibility

`schema_version` is a namespaced identifier with a trailing major version, e.g.
`agent-metrics/structural-health/v1`. Each record type is versioned
**independently** — structural health and effectiveness carry their own
`schema_version` and bump on their own clock.

### When to bump

Bump the trailing version (`.../v1` → `.../v2`) when a record's shape changes in
a way a consumer must distinguish:

- Removing or renaming a field.
- Changing a field's type or the meaning of its value.
- Changing the deduplication key or identity semantics.

Do **not** bump for backward-compatible additions — most importantly a new
**optional** field (the way `correlation_id` was added to `v1`). Additive
optional fields do not change how existing consumers read a record.

### Consumer compatibility contract

To make additive changes safe without a version bump, consumers must:

- **Ignore unknown fields.** A record may contain fields a consumer does not
  recognize; they must be tolerated, not rejected.
- **Tolerate missing optional fields.** An optional field (for example
  `correlation_id`) may be absent; treat absence as "unset".

A `schema_version` change is therefore a deliberate signal that these guarantees
no longer hold and the consumer must branch on the version.

### Independence from `tool_version`

`schema_version` is not tied to the package version. A package release
(`tool_version` bump) never changes `schema_version`, and a schema change never
requires a particular package version. Because dedupe keys include
`schema_version` but never `tool_version`, a package release never fractures a
dedupe series and a schema bump intentionally starts a new one. See
[releasing.md](releasing.md#relationship-to-schema_version) for the package
versioning policy.

## Provenance envelope

Every record — structural health or effectiveness — includes these fields.

| Field            | Type            | Role     | Notes                                                                 |
| ---------------- | --------------- | -------- | --------------------------------------------------------------------- |
| `schema_version` | string          | identity | Versioned schema id, e.g. `agent-metrics/structural-health/v1`.       |
| `remote_url`     | string \| null  | identity | Remote repository URL (`origin`). Durable identity, not the path.     |
| `commit`         | string \| null  | identity | HEAD commit SHA. Durable identity.                                    |
| `bundle`         | string          | identity | Identifier of the measured bundle (e.g. `okf-core`).                  |
| `branch`         | string \| null  | context  | Current branch. Context only — excluded from the dedupe key.          |
| `dirty`          | boolean         | context  | Whether the worktree had uncommitted changes.                         |
| `host`           | string          | context  | Machine that produced the record.                                     |
| `environment`    | string          | context  | `ci` when a CI environment flag is set, otherwise `local`.            |
| `durability`     | string          | context  | `durable` (clean commit measured by CI) or `advisory` (everything else). |
| `timestamp`      | string          | context  | ISO 8601 UTC; honors `SOURCE_DATE_EPOCH` for reproducible runs.       |
| `tool_version`   | string          | context  | Version of `agent-metrics` that wrote the record.                     |

**Durable identity vs. context.** The remote URL and commit SHA are the durable
identity of a measurement; branch and host are context that varies between
checkouts of the same commit. Deduplication keys therefore rely on identity
fields and deliberately ignore branch and host.

**Durability.** A record is `durable` only when it measures a clean commit
inside a CI environment — for example, the health snapshot run on merge to the
default branch. These are the settled evidence of record. Local or dirty runs
are `advisory`: useful for a quick pre-change signal, but not authoritative.

## Structural health records

Cheap, mechanical snapshots (concept counts, orphans, broken links, degree,
duplicate candidates, stale provenance). They should run continuously. Written
by `agent-metrics health --append` to `.agent-metrics/health.jsonl`.

- **Schema:** `agent-metrics/structural-health/v1`
- **Dedupe key:** `(remote_url, bundle, commit, schema_version)`

The provenance envelope plus a `metrics` object of the measured values:

```jsonl
{"branch":"main","bundle":"okf-core","commit":"b0ebdda43b809cf851fa3ed55e9fcf9ee71306d5","dirty":false,"durability":"durable","environment":"ci","host":"ci-runner-7","metrics":{"broken_links":0,"concepts":128,"duplicate_candidates":4,"orphans":3},"remote_url":"https://github.com/xchewtoyx/agent-metrics.git","schema_version":"agent-metrics/structural-health/v1","timestamp":"2026-07-18T20:58:50Z","tool_version":"0.1.0"}
{"branch":"feature/lens-split","bundle":"okf-core","commit":"1f9c0a2","dirty":true,"durability":"advisory","environment":"local","host":"laptop","metrics":{"broken_links":2,"concepts":130,"duplicate_candidates":5,"orphans":3},"remote_url":"https://github.com/xchewtoyx/agent-metrics.git","schema_version":"agent-metrics/structural-health/v1","timestamp":"2026-07-18T21:04:12Z","tool_version":"0.1.0"}
```

Two records for the same `okf-core` bundle at the same commit collapse to one
under the dedupe key regardless of the branch or host that produced them.

## Effectiveness records

Judgment-heavy A/B replay outcomes: did a pack, lens, routing rule, guardrail,
or schema change actually improve agent outcomes? They should run only when a
shared, load-bearing surface changes. Built via
`agent_metrics.build_effectiveness_envelope(...)`.

- **Schema:** `agent-metrics/effectiveness/v1`
- **Dedupe key:** `(remote_url, bundle, commit, schema_version, model,
  harness_version, task_set, run_index, experiment_arms)`

Effectiveness records extend the provenance envelope with the experiment
coordinates needed to compare arms and replays:

| Field             | Type              | Notes                                              |
| ----------------- | ----------------- | -------------------------------------------------- |
| `model`           | string            | Model under test.                                  |
| `harness_version` | string            | Agent harness version.                             |
| `task_set`        | string            | Task set / benchmark identifier.                   |
| `run_index`       | integer           | Replay index, so repeated runs stay distinct.      |
| `experiment_arms` | list of strings   | Experiment arms compared in this record.           |
| `metrics`         | object            | Measured outcomes.                                 |

```jsonl
{"branch":"main","bundle":"okf-core","commit":"b0ebdda","dirty":false,"durability":"durable","environment":"ci","experiment_arms":["control","treatment"],"harness_version":"1.4.0","host":"ci-runner-7","metrics":{"solved":41,"total":50},"model":"claude","remote_url":"https://github.com/xchewtoyx/agent-metrics.git","run_index":0,"schema_version":"agent-metrics/effectiveness/v1","task_set":"swe-bench-lite","timestamp":"2026-07-18T22:00:00Z","tool_version":"0.1.0"}
{"branch":"main","bundle":"okf-core","commit":"b0ebdda","dirty":false,"durability":"durable","environment":"ci","experiment_arms":["control","treatment"],"harness_version":"1.4.0","host":"ci-runner-7","metrics":{"solved":39,"total":50},"model":"claude","remote_url":"https://github.com/xchewtoyx/agent-metrics.git","run_index":1,"schema_version":"agent-metrics/effectiveness/v1","task_set":"swe-bench-lite","timestamp":"2026-07-18T22:11:30Z","tool_version":"0.1.0"}
```

The two records above share every identity field except `run_index`, so both
replays are preserved rather than deduplicated.

## Correlation

Any record may carry an optional `correlation_id`. It is omitted unless supplied
and ties related records into a single timeline — for example a wrapper block
and its later recovery, or every record produced within one agent session. On
export it maps to the OpenTelemetry `gen_ai.conversation.id` attribute.

## OpenTelemetry alignment

agent-metrics keeps its on-disk JSONL schema stable and self-describing, and
maps to OpenTelemetry semantic conventions only at the *export boundary* via
`agent_metrics.to_otel_attributes(record)`. The `vcs.*` conventions are Release
Candidate and the `gen_ai.*` conventions are still evolving in their own
semantic-conventions repository, so the durable evidence on disk is deliberately
not coupled to them; the `schema_version` field is the versioning contract
instead.

The mapping reuses existing conventions where they fit and reserves the
`agent_metrics.*` namespace for concepts OpenTelemetry does not yet cover, so our
fields never collide with a future standard attribute:

| Record field     | OpenTelemetry attribute        | Notes                                        |
| ---------------- | ------------------------------ | -------------------------------------------- |
| `remote_url`     | `vcs.repository.url.full`      | VCS (RC).                                     |
| `commit`         | `vcs.ref.head.revision`        | VCS (RC).                                     |
| `branch`         | `vcs.ref.head.name`            | VCS (RC).                                     |
| `host`           | `host.name`                    | OTel Resource attribute.                      |
| `tool_version`   | `service.version`             | Resource; service is agent-metrics.          |
| `correlation_id` | `gen_ai.conversation.id`       | GenAI (evolving); omitted when unset.         |
| `model`          | `gen_ai.request.model`         | GenAI (evolving).                             |
| `harness_version`| `gen_ai.agent.version`         | GenAI (evolving).                             |
| `schema_version` | `agent_metrics.schema_version` | No stable OTel home → reserved namespace.     |
| `bundle`         | `agent_metrics.bundle`         | Reserved namespace.                           |
| `dirty`          | `agent_metrics.dirty`          | Reserved namespace.                           |
| `environment`    | `agent_metrics.environment`    | Coarser than `deployment.environment.name`.   |
| `durability`     | `agent_metrics.durability`     | Reserved namespace.                           |
| `task_set`       | `agent_metrics.task_set`       | Reserved namespace.                           |
| `run_index`      | `agent_metrics.run_index`      | Reserved namespace.                           |
| `experiment_arms`| `agent_metrics.experiment_arms`| Reserved namespace; array of strings.         |

Two fields are intentionally **not** exported as attributes:

* `timestamp` becomes the span/log timestamp of the exported record.
* `metrics` values map to OpenTelemetry metric data points, not span attributes.

Fields with a `None` value (for example `commit` outside a git checkout) are
omitted from the attribute set. Any future field that is not in the mapping table
is exported under `agent_metrics.*` automatically, so new concepts stay
namespace-safe by default.

### Why align: standard sidecars over bespoke integrations

Integrating specific telemetry backends is deliberately **out of scope**.
agent-metrics writes plain JSONL and stops there — it does not ship, poll, or
push to any observability API. That keeps the tool small and its evidence
portable.

Standard alignment is what lets that scope hold without foreclosing publication
or analysis. Because the export boundary speaks OpenTelemetry semantic
conventions, an adopter who wants dashboards, alerting, or long-term storage can
point a standard, off-the-shelf collector — Grafana Alloy, the OpenTelemetry
Collector, or any OTLP-speaking agent — at the output as a **sidecar**, rather
than each adopter writing a bespoke local integration against a particular
vendor. The common standard is the seam: it moves backend integration out of
this codebase and into commodity, reusable infrastructure.

Keep this in mind when adding or changing outputs. Prefer shapes and attribute
names that a standard sidecar can consume unmodified over anything that would
require custom glue on the consumer side — the value of not integrating a
backend depends on the output staying standard enough that a sidecar can.
