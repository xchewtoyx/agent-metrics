"""Utilities for measuring agent and knowledge-repo changes."""

from __future__ import annotations

from agent_metrics.health import (
    AgentMetricsError,
    append_health_record,
    capture_health,
    create_health_envelope,
    load_metrics,
    parse_metric_value,
    parse_metrics_definitions,
)
from agent_metrics.provenance import (
    ADVISORY,
    AGENT_METRICS_NAMESPACE,
    DEFAULT_BUNDLE,
    DURABLE,
    EFFECTIVENESS_SCHEMA_VERSION,
    STRUCTURAL_HEALTH_SCHEMA_VERSION,
    build_effectiveness_envelope,
    build_provenance,
    classify_durability,
    detect_environment,
    effectiveness_dedupe_key,
    get_git_metadata,
    get_host,
    structural_health_dedupe_key,
    to_otel_attributes,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "ADVISORY",
    "AGENT_METRICS_NAMESPACE",
    "AgentMetricsError",
    "DEFAULT_BUNDLE",
    "DURABLE",
    "EFFECTIVENESS_SCHEMA_VERSION",
    "STRUCTURAL_HEALTH_SCHEMA_VERSION",
    "append_health_record",
    "build_effectiveness_envelope",
    "build_provenance",
    "capture_health",
    "classify_durability",
    "create_health_envelope",
    "detect_environment",
    "effectiveness_dedupe_key",
    "get_git_metadata",
    "get_host",
    "load_metrics",
    "parse_metric_value",
    "parse_metrics_definitions",
    "structural_health_dedupe_key",
    "to_otel_attributes",
]
