"""Command-line interface for agent-metrics."""

from __future__ import annotations

import json
from typing import Any

import click

from agent_metrics import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="agent-metrics")
def main() -> None:
    """Measure agent and knowledge-repo changes with plain-file evidence."""


def _parse_val(val_str: str) -> int | float | str:
    import math

    try:
        return int(val_str)
    except ValueError:
        try:
            value = float(val_str)
            if not math.isfinite(value):
                raise click.BadParameter(
                    f"Metric value '{val_str}' must be a finite number."
                )
            return value
        except ValueError:
            return val_str


def _load_input_file(input_file: Any | None) -> dict[str, Any]:
    if input_file is None:
        return {}
    try:
        file_data = json.load(input_file)
        if not isinstance(file_data, dict):
            raise click.ClickException("Metrics input file must be a JSON object.")
        return file_data
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in metrics input: {e}") from e


def _parse_metrics(metrics: tuple[str, ...]) -> dict[str, Any]:
    parsed = {}
    for metric in metrics:
        if "=" not in metric:
            raise click.BadParameter(f"Metric '{metric}' must be in KEY=VALUE format.")
        key, val_str = metric.split("=", 1)
        key = key.strip()
        if not key:
            raise click.BadParameter("Metric key cannot be empty.")
        parsed[key] = _parse_val(val_str.strip())
    return parsed


@main.command()
@click.option(
    "--append",
    "append",
    is_flag=True,
    help="Append a structural health snapshot to .agent-metrics/health.jsonl.",
)
@click.option(
    "--metric",
    "-m",
    "metrics",
    multiple=True,
    help="Explicit metric in KEY=VALUE format (can be specified multiple times).",
)
@click.option(
    "--input-file",
    "-i",
    "input_file",
    type=click.File("r"),
    help="Path to JSON file containing metrics (use - for stdin).",
)
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
)
def health(
    append: bool,
    metrics: tuple[str, ...],
    input_file: Any | None,
    directory: str,
) -> None:
    """Record objective structural health for a repository or bundle."""
    from agent_metrics.health import append_health_record, create_health_envelope

    merged_metrics = _load_input_file(input_file)
    parsed_metrics = _parse_metrics(metrics)
    merged_metrics.update(parsed_metrics)

    record = create_health_envelope(merged_metrics, directory, __version__)
    try:
        record_str = json.dumps(
            record,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        )
    except ValueError as e:
        raise click.ClickException(f"Metrics contain non-JSON values: {e}") from e

    if append:
        append_health_record(directory, record)
    click.echo(record_str)


@main.command()
def contract() -> None:
    """Scaffold a pre-change prediction for load-bearing edits."""
    _not_implemented("contract")


@main.command()
def settle() -> None:
    """Settle a change contract with evidence and a verdict."""
    _not_implemented("settle")


@main.command()
def audit() -> None:
    """Report whether contracts and settlements exist for relevant changes."""
    _not_implemented("audit")


@main.command()
def roll() -> None:
    """Aggregate JSONL evidence across repositories and commits."""
    _not_implemented("roll")


def _not_implemented(command: str, **_: object) -> None:
    raise click.ClickException(
        f"`agent-metrics {command}` is a project skeleton command and is not "
        "implemented yet."
    )
