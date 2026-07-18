"""Logic for metric-agnostic health snapshots."""

from __future__ import annotations

import contextlib
import json
import math
import os
import subprocess
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


class AgentMetricsError(ValueError):
    """Base exception for agent-metrics library errors."""

    pass


def get_git_metadata(repo_path: str = ".") -> dict[str, Any]:
    """Resolve git metadata for the given repository path.

    Returns a dictionary with keys: 'commit', 'remote_url', 'dirty', 'durable'.
    """
    commit = None
    remote_url = None
    dirty = True
    durable = False

    abs_path = os.path.abspath(repo_path)

    try:
        # Check if we are inside a git worktree
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=abs_path,
            capture_output=True,
            text=True,
            check=True,
        )
        if res.stdout.strip() == "true":
            # Get commit
            res_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=abs_path,
                capture_output=True,
                text=True,
            )
            if res_commit.returncode == 0:
                commit = res_commit.stdout.strip()

            # Get remote URL
            res_remote = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=abs_path,
                capture_output=True,
                text=True,
            )
            if res_remote.returncode == 0:
                remote_url = res_remote.stdout.strip()

            # Get status (dirty check)
            res_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=abs_path,
                capture_output=True,
                text=True,
            )
            if res_status.returncode == 0:
                dirty = bool(res_status.stdout.strip())
                durable = not dirty
    except (subprocess.SubprocessError, FileNotFoundError):
        # Gracefully handle non-git environments
        pass

    return {
        "commit": commit,
        "remote_url": remote_url,
        "dirty": dirty,
        "durable": durable,
    }


def create_health_envelope(
    metrics: dict[str, Any],
    directory: str = ".",
    tool_version: str = "0.1.0",
) -> dict[str, Any]:
    """Wraps user metrics in a git envelope with a current timestamp."""
    git_meta = get_git_metadata(directory)

    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    timestamp_dt = datetime.now(UTC)
    if source_date_epoch is not None:
        with contextlib.suppress(ValueError, OverflowError, OSError):
            timestamp_dt = datetime.fromtimestamp(int(source_date_epoch), tz=UTC)
    timestamp = timestamp_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "timestamp": timestamp,
        "commit": git_meta["commit"],
        "remote_url": git_meta["remote_url"],
        "dirty": git_meta["dirty"],
        "durable": git_meta["durable"],
        "tool_version": tool_version,
        "metrics": metrics,
    }


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

    record = create_health_envelope(merged_metrics, directory, tool_version)

    # Validate strict JSON by dumps-ing first
    json.dumps(record, sort_keys=True, allow_nan=False)

    if append:
        append_health_record(directory, record)

    return record
