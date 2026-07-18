import pytest
from click.testing import CliRunner

from agent_metrics.cli import main


def test_help_explains_project_aim() -> None:
    """The CLI should describe the project before feature work exists."""
    result = CliRunner().invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "plain-file evidence" in result.output
    assert "health" in result.output
    assert "contract" in result.output


def test_version_uses_project_name() -> None:
    result = CliRunner().invoke(main, ["--version"])

    assert result.exit_code == 0
    assert result.output.startswith("agent-metrics, version ")


@pytest.mark.parametrize("command", ["health", "contract", "settle", "audit", "roll"])
def test_skeleton_command_fails_clearly(command: str) -> None:
    """Negative case: command stubs must fail honestly until implemented."""
    args = [command, "--append"] if command == "health" else [command]

    result = CliRunner().invoke(main, args)

    assert result.exit_code != 0
    assert "not implemented yet" in result.output


def test_unknown_command_is_rejected() -> None:
    result = CliRunner().invoke(main, ["unknown-command"])

    assert result.exit_code != 0
    assert "No such command" in result.output
