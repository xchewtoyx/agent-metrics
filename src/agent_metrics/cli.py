"""Command-line interface for agent-metrics."""

from __future__ import annotations

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
    help="Append a structural health snapshot to .agent-metrics/health.jsonl.",
)
def health(append: bool) -> None:
    """Record objective structural health for a repository or bundle."""
    _not_implemented("health", append=append)


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
