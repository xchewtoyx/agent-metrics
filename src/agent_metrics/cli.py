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


@main.command()
@click.option(
    "--append",
    "append",
    is_flag=True,
    help="Append a health snapshot to .agent-metrics/health.jsonl.",
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
    from agent_metrics.health import (
        AgentMetricsError,
        capture_health,
        parse_metrics_definitions,
    )

    try:
        parsed_metrics = parse_metrics_definitions(metrics)
    except ValueError as e:
        raise click.BadParameter(str(e)) from e

    try:
        record = capture_health(
            directory=directory,
            metrics=parsed_metrics,
            input_file=input_file,
            append=append,
            tool_version=__version__,
        )
        record_str = json.dumps(
            record,
            separators=(",", ":"),
            sort_keys=True,
            allow_nan=False,
        )
    except AgentMetricsError as e:
        raise click.ClickException(f"Invalid metrics input: {e}") from e
    except TypeError as e:
        raise click.ClickException(f"Type error: {e}") from e
    except json.JSONDecodeError as e:
        raise click.ClickException(f"Invalid JSON in metrics input: {e}") from e
    except ValueError as e:
        raise click.ClickException(f"Metrics contain non-JSON values: {e}") from e

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
