# API Conventions

Reference for anyone adding to the `agent_metrics` library. Load this when
touching the public API or naming a new function. The goal is a surface that
reads as one system, so a caller can guess a function's behavior from its name.

## Naming verbs

Name functions by what they do, using the established verbs below. Consistency
here is load-bearing: it keeps the public surface predictable and prevents drift
(for example, a stray `create_*` next to the `build_*` family).

| Verb | Contract | Examples |
| --- | --- | --- |
| `build_*` | Assemble and return a record/envelope dict. May read ambient facts (git, host, clock); does not persist. | `build_provenance`, `build_health_envelope`, `build_effectiveness_envelope` |
| `capture_*` | High-level orchestration: gather inputs, build a record, optionally persist. | `capture_health` |
| `get_*` | Read ambient facts from the environment. Degrade gracefully; never raise. | `get_git_metadata` |
| `parse_*` | Convert strings / CLI input to typed Python. Raise `AgentMetricsError` on bad input. | `parse_metric_value`, `parse_metrics_definitions` |
| `load_*` | Read structured data from a file, stream, or dict. | `load_metrics` |
| `append_*` | Write a record to append-only JSONL. | `append_health_record` |
| `scaffold_*` | Create a filesystem scaffold with deterministic naming and collision checks. | `scaffold_contract` |
| `settle_*` | Record the final outcome for a previously scaffolded prediction without rewriting the prediction body. | `settle_contract` |
| `to_*` | Pure transform/export to another representation. | `to_otel_attributes` |
| `*_dedupe_key` | Return the identity tuple for a record type. | `structural_health_dedupe_key`, `effectiveness_dedupe_key` |
| `detect_*` / `classify_*` / `resolve_*` | Internal derivations of a single field. **Keep out of `__all__`.** | `detect_environment`, `classify_durability`, `resolve_timestamp` |

If a new function does not fit a verb above, prefer adding a documented verb here
over inventing a one-off name.

## Public gateway

- `src/agent_metrics/__init__.py`'s `__all__` is the **strict** public API. Export
  only what an external consumer needs to call.
- Intermediate building blocks stay module-level in their submodule and out of
  `__all__` (they are still importable as `agent_metrics.<module>.<name>` for
  internal use and tests). Do not publish a helper just because it exists.
- Before adding a name to `__all__`, ask: would a third-party integrator call
  this directly, or is it a step of something they already call?

## Function shape

- Public functions carry type hints and a docstring describing behavior.
- Return plain structures — dicts, lists, tuples, dataclasses — not CLI-specific
  constructs or mutable global state.
- Raise `AgentMetricsError` (from `agent_metrics.errors`) or a subclass for
  expected domain validation and runtime failures. The CLI layer maps these to
  user-facing messages; library functions do not print or exit.
- Keep the CLI (`cli.py`) a thin argument/option parsing and presentation layer.
  All logic lives in library modules.
- A function that documents graceful degradation (typically a `get_*`) catches
  the **base** exception (e.g. `OSError`), not hand-picked subclasses, so new
  failure modes stay handled. Pin the guarantee with a test over the family (see
  [test_invariants.py](../tests/test_invariants.py)), not one instance.
- Defaults that represent a derived or shared fact — version, host, timestamp —
  resolve from a single helper (parameter default `None`), never a per-signature
  literal, so they cannot drift between call sites (e.g. `tool_version`).
- Docstrings and CLI help describe what the code does *now*, not what it aspires
  to. When you rename or repurpose a symbol, update its references in `docs/`.

## Records and provenance

- Every JSONL record is built through the provenance envelope
  (`build_provenance`) and carries a versioned `schema_version`. See
  [schemas.md](schemas.md).
- Deduplication is commit-keyed, never path-keyed. Branch and host are context.
- Map to OpenTelemetry attribute names only at the export boundary
  (`to_otel_attributes`); keep the on-disk JSONL schema stable and self-describing.
