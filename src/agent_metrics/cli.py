"""Command-line interface for agent-metrics."""

from __future__ import annotations

import json
from typing import Any

import click

from agent_metrics import __version__
from agent_metrics.provenance import DEFAULT_BUNDLE


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
@click.option(
    "--bundle",
    "-b",
    "bundle",
    default=DEFAULT_BUNDLE,
    show_default=True,
    help="Identifier of the measured bundle; part of the dedupe identity.",
)
@click.option(
    "--correlation-id",
    "correlation_id",
    default=None,
    help="Optional id tying related records into one timeline "
    "(maps to gen_ai.conversation.id on OTLP export).",
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
    bundle: str,
    correlation_id: str | None,
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
            bundle=bundle,
            correlation_id=correlation_id,
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
@click.option(
    "--slug",
    "slug",
    default=None,
    help="Explicit lower_snake_case filename slug. Defaults to the title slug.",
)
@click.option(
    "--number",
    "number",
    type=click.IntRange(1, 9999),
    default=None,
    help="Explicit four-digit contract number. Defaults to the next number.",
)
@click.option(
    "--directory",
    "-C",
    "directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    show_default=True,
    help="Repository root where .agent-metrics/contracts lives.",
)
@click.argument("title")
def contract(title: str, slug: str | None, number: int | None, directory: str) -> None:
    """Scaffold a pre-change prediction for load-bearing edits."""
    from agent_metrics.contracts import scaffold_contract
    from agent_metrics.errors import AgentMetricsError

    try:
        scaffold = scaffold_contract(
            title=title,
            directory=directory,
            slug=slug,
            number=number,
        )
    except AgentMetricsError as e:
        raise click.ClickException(f"Invalid contract input: {e}") from e

    click.echo(str(scaffold.path))


@main.command()
@click.option(
    "--verdict",
    "verdict",
    required=True,
    help="Settlement verdict: KEEP, IMPROVE, or ROLLBACK.",
)
@click.option(
    "--evidence",
    "evidence",
    required=True,
    help="Evidence summary supporting the settlement verdict.",
)
@click.option(
    "--directory",
    "-C",
    "directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    show_default=True,
    help="Repository root where .agent-metrics/contracts lives.",
)
@click.argument("contract_ref")
def settle(contract_ref: str, verdict: str, evidence: str, directory: str) -> None:
    """Settle a change contract with evidence and a verdict."""
    from agent_metrics.contracts import settle_contract
    from agent_metrics.errors import AgentMetricsError

    try:
        settlement = settle_contract(
            contract_ref,
            verdict=verdict,
            evidence=evidence,
            directory=directory,
        )
    except AgentMetricsError as e:
        raise click.ClickException(f"Invalid settlement input: {e}") from e

    click.echo(str(settlement.path))


@main.command()
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json"]),
    default="json",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--directory",
    "-C",
    "directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    show_default=True,
    help="Repository root where .agent-metrics/contracts lives.",
)
def audit(output_format: str, directory: str) -> None:
    """Report file-based contract and settlement counts as JSON."""
    from agent_metrics.contracts import audit_contracts

    report = audit_contracts(directory=directory)
    if output_format == "json":
        click.echo(
            json.dumps(
                report.to_dict(),
                separators=(",", ":"),
                sort_keys=True,
            )
        )


@main.command()
def roll() -> None:
    """Aggregate JSONL evidence across repositories and commits."""
    _not_implemented("roll")


def _not_implemented(command: str, **_: object) -> None:
    raise click.ClickException(
        f"`agent-metrics {command}` is a project skeleton command and is not "
        "implemented yet."
    )
