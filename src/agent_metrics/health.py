"""Logic for metric-agnostic structural health snapshots."""

from __future__ import annotations

import json
import math
import os
from typing import TYPE_CHECKING

from agent_metrics.provenance import (
    DEFAULT_BUNDLE,
    STRUCTURAL_HEALTH_SCHEMA_VERSION,
    build_provenance,
)

if TYPE_CHECKING:
    from typing import Any


class AgentMetricsError(ValueError):
    """Base exception for agent-metrics library errors."""

    pass


def create_health_envelope(
    metrics: dict[str, Any],
    directory: str = ".",
    tool_version: str = "0.1.0",
    bundle: str = DEFAULT_BUNDLE,
) -> dict[str, Any]:
    """Wrap structural health metrics in the versioned provenance envelope."""
    record = build_provenance(
        STRUCTURAL_HEALTH_SCHEMA_VERSION,
        bundle=bundle,
        directory=directory,
        tool_version=tool_version,
    )
    record["metrics"] = metrics
    return record


def append_health_record(directory: str, record: dict[str, Any]) -> str:
    """Appends a health record to the health.jsonl file under the target directory.

    Creates target directories if they do not exist. Returns the path of the file.
    """
    target_dir = os.path.join(directory, ".agent-metrics")
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, "health.jsonl")

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                record,
                separators=(",", ":"),
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        )

    return file_path


def load_metrics(input_source: Any) -> dict[str, Any]:
    """Load metrics from a JSON file path, file-like object, or dictionary."""
    if input_source is None:
        return {}
    if isinstance(input_source, dict):
        return dict(input_source)

    if isinstance(input_source, (str, bytes, os.PathLike)):
        with open(input_source, encoding="utf-8") as f:
            data = json.load(f)
    elif hasattr(input_source, "read"):
        data = json.load(input_source)
    else:
        raise TypeError("Unsupported metrics input source type.")

    if not isinstance(data, dict):
        raise AgentMetricsError("Metrics input file must be a JSON object.")
    return data


def parse_metric_value(val_str: str) -> int | float | str:
    """Parse a string value into a typed int, float, or string.

    Raises AgentMetricsError if a float is not finite.
    """
    try:
        return int(val_str)
    except ValueError:
        pass

    try:
        value = float(val_str)
    except ValueError:
        return val_str

    if not math.isfinite(value):
        raise AgentMetricsError(f"Metric value '{val_str}' must be a finite number.")
    return value


def parse_metrics_definitions(
    definitions: list[str] | tuple[str, ...],
) -> dict[str, Any]:
    """Parse a sequence of KEY=VALUE strings into a dictionary of typed metrics."""
    parsed = {}
    for definition in definitions:
        if "=" not in definition:
            raise AgentMetricsError(
                f"Metric '{definition}' must be in KEY=VALUE format."
            )
        key, val_str = definition.split("=", 1)
        key = key.strip()
        if not key:
            raise AgentMetricsError("Metric key cannot be empty.")
        parsed[key] = parse_metric_value(val_str.strip())
    return parsed


def capture_health(
    directory: str = ".",
    metrics: dict[str, Any] | None = None,
    input_file: Any | None = None,
    append: bool = False,
    tool_version: str = "0.1.0",
    bundle: str = DEFAULT_BUNDLE,
) -> dict[str, Any]:
    """Capture codebase health metrics wrapped in a git provenance envelope.

    Merges metrics from the optional dictionary and/or input file.
    If append is True, appends the serialized envelope to .agent-metrics/health.jsonl.
    """
    merged_metrics = {}
    if input_file is not None:
        merged_metrics.update(load_metrics(input_file))
    if metrics is not None:
        merged_metrics.update(metrics)

    record = create_health_envelope(merged_metrics, directory, tool_version, bundle)

    # Validate strict JSON by dumps-ing first
    json.dumps(record, sort_keys=True, allow_nan=False)

    if append:
        append_health_record(directory, record)

    return record
