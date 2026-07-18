# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- OpenTelemetry alignment for the JSONL schemas: a `to_otel_attributes` export helper mapping records onto `vcs.*`, `gen_ai.*`, `host.*`, and `service.*` semantic conventions, a reserved `agent_metrics.*` namespace (`AGENT_METRICS_NAMESPACE`) for concepts OTel does not cover, and an optional `correlation_id` envelope field (also exposed as `health --correlation-id`) mapping to `gen_ai.conversation.id`.
- Versioned JSONL schemas and a shared provenance envelope in a new `provenance` module, defining the durable identity (remote URL, commit SHA, bundle) and context (branch, host, environment, durability) carried by every record.
- Structural health (`agent-metrics/structural-health/v1`) and effectiveness (`agent-metrics/effectiveness/v1`) record schemas, with `structural_health_dedupe_key` and `effectiveness_dedupe_key` helpers and a `build_effectiveness_envelope` builder.
- Durability classification distinguishing `durable` CI-on-clean-commit records from `advisory` local or dirty runs.
- `--bundle`/`-b` option on `health` to name the measured bundle as part of the dedupe identity.
- Schema and example JSONL documentation in [docs/schemas.md](docs/schemas.md).
- Dogfooded change contract `0003_jsonl_schemas.md` under `.agent-metrics/contracts/`.
- Metric-agnostic codebase health snapshot command `health --append` supporting standard file inputs and CLI parameter overrides.
- Git telemetry extraction logic capturing remote URL, current commit hash, dirty workspace flag, and durability/provenance status.
- Verification test suite covering git boundary conditions, serialization errors, and parameter parsing constraints.
- Dogfooded change contracts `0001_initial_milestone.md` and `0002_health_command.md` under `.agent-metrics/contracts/`.
- Structured Python library API exposing `capture_health`, `load_metrics`, `parse_metric_value`, `parse_metrics_definitions`, and `AgentMetricsError` to support third-party programmatic extensions.

### Changed
- Structural health records now conform to the versioned provenance envelope: they include `schema_version`, `branch`, `bundle`, `host`, `environment`, and `durability`, replacing the previous boolean `durable` field.
- Moved git metadata resolution and timestamp handling into the `provenance` module; `get_git_metadata` now also reports the current `branch`.
- Refactored CLI execution endpoints in `cli.py` to act as lightweight argument/option parsing wrappers delegating to the library API.
- Updated agent instructions (`AGENTS.md`) with explicit project layout guidelines, modular API design principles, design simplification rules, and the Boy Scout Rule.

### Fixed
- `create_health_envelope` now suppresses `OverflowError` and `OSError` in addition to `ValueError` when parsing `SOURCE_DATE_EPOCH`, preventing crashes on out-of-range epoch values set by users or CI environments.


## [0.1.0] - 2026-07-18
- Initial project skeleton containing Click CLI setup, testing harness, and development workflow parameters.

[Unreleased]: https://github.com/xchewtoyx/agent-metrics/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/xchewtoyx/agent-metrics/releases/tag/v0.1.0
