# JSONL Schemas and Provenance Envelope

`agent-metrics` records are newline-delimited JSON (JSONL): one self-describing
record per line, grep-able, committable, and mergeable without a service or
database. Every record carries a **provenance envelope** so that the same bundle
measured at the same commit deduplicates cleanly across local checkouts, hosts,
branches, and CI runs.

Records are versioned. The `schema_version` field names the record shape so
consumers can evolve their handling as schemas change. Bump the trailing version
(`.../v1` → `.../v2`) whenever a record's shape changes in a way consumers must
distinguish.

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
