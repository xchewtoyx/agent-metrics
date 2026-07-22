"""Utilities for measuring agent and knowledge-repo changes."""

from __future__ import annotations

from agent_metrics.contracts import (
    ContractAudit,
    ContractScaffold,
    ContractSettlement,
    audit_contracts,
    scaffold_contract,
    settle_contract,
)
from agent_metrics.errors import AgentMetricsError
from agent_metrics.health import (
    append_health_record,
    build_health_envelope,
    capture_health,
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
    _resolve_tool_version,
    build_effectiveness_envelope,
    build_provenance,
    effectiveness_dedupe_key,
    get_git_metadata,
    structural_health_dedupe_key,
    to_otel_attributes,
)

__version__ = _resolve_tool_version()

__all__ = [
    "__version__",
    "ADVISORY",
    "AGENT_METRICS_NAMESPACE",
    "AgentMetricsError",
    "ContractAudit",
    "ContractScaffold",
    "ContractSettlement",
    "DEFAULT_BUNDLE",
    "DURABLE",
    "EFFECTIVENESS_SCHEMA_VERSION",
    "STRUCTURAL_HEALTH_SCHEMA_VERSION",
    "append_health_record",
    "audit_contracts",
    "build_effectiveness_envelope",
    "build_health_envelope",
    "build_provenance",
    "capture_health",
    "effectiveness_dedupe_key",
    "get_git_metadata",
    "load_metrics",
    "parse_metric_value",
    "parse_metrics_definitions",
    "scaffold_contract",
    "settle_contract",
    "structural_health_dedupe_key",
    "to_otel_attributes",
]
