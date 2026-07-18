# Review Checklist

Repo-specific gates to apply when reviewing (or self-reviewing) a change, on top
of the general questions in [AGENTS.md](../AGENTS.md) and the built-in `/review`
skill. Load this when reviewing a diff or preparing one for review.

## Process

- [ ] **Contract present for load-bearing changes.** A harness or knowledge edit
      that changes behavior has a `.agent-metrics/contracts/NNNN_slug.md` contract.
      Pure docs or trivial refactors do not.
- [ ] **CHANGELOG updated.** User- or contributor-facing changes are recorded
      under `[Unreleased]` using Keep a Changelog conventions.
- [ ] **Prose describes current behavior, not aspirations.** Docstrings, CLI help,
      and docs do not overclaim (e.g. "no I/O" on a function that reads git/env,
      or "structural" on a metric-agnostic recorder).

## Schema and provenance

- [ ] **Every JSONL record goes through the provenance envelope** and carries a
      versioned `schema_version` (see [schemas.md](schemas.md)).
- [ ] **Deduplication is commit-keyed, not path-keyed.** Branch and host are
      context, excluded from dedupe keys.
- [ ] **OpenTelemetry mapping stays at the export boundary** (`to_otel_attributes`).
      The on-disk JSONL schema is not coupled to `vcs.*` / `gen_ai.*` names, and
      novel fields use the reserved `agent_metrics.*` namespace.

## API surface

- [ ] **`__all__` is minimal.** New exports are things an external consumer calls,
      not internal building blocks. See [api-conventions.md](api-conventions.md).
- [ ] **Naming follows the verb guide.** No stray verbs (for example `create_*`
      beside the `build_*` family).
- [ ] **Errors are decoupled from presentation.** Library code raises
      `AgentMetricsError`; only the CLI maps errors to user-facing messages.
- [ ] **Renamed a public symbol?** Grep `docs/`, `README.md`, and `CHANGELOG.md`
      for the old name (change contracts are point-in-time records — excluded).

## Tests and checks

- [ ] **Documented guarantees are asserted, not just executed.** "Never raises" /
      graceful degradation, determinism, single-source version, and the documented
      record shape each have a test that pins the guarantee. **100% line coverage
      is necessary but not the bar** — every defect found in review so far shipped
      with full coverage. See [test_invariants.py](../tests/test_invariants.py).
- [ ] **Robustness is tested across the failure family.** A function that
      documents graceful degradation catches the base exception (e.g. `OSError`),
      not hand-picked subclasses, and a test exercises the family, not one instance.
- [ ] **Positive and negative cases covered.** Success proves the happy path; bad
      input fails clearly and is asserted.
- [ ] **`black`, `ruff`, and `pytest` pass.**
