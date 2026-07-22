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


@pytest.mark.parametrize("command", ["settle", "audit", "roll"])
def test_skeleton_command_fails_clearly(command: str) -> None:
    """Negative case: command stubs must fail honestly until implemented."""
    args = [command]

    result = CliRunner().invoke(main, args)

    assert result.exit_code != 0
    assert "not implemented yet" in result.output


def test_contract_command_scaffolds_file(tmp_path) -> None:
    result = CliRunner().invoke(
        main,
        ["contract", "--directory", str(tmp_path), "Measure Harness Drift"],
    )

    assert result.exit_code == 0
    assert result.output.strip().endswith(
        ".agent-metrics/contracts/0001_measure_harness_drift.md"
    )
    contract = (
        tmp_path / ".agent-metrics" / "contracts" / "0001_measure_harness_drift.md"
    )
    assert contract.exists()
    text = contract.read_text(encoding="utf-8")
    assert "# Change Contract: 0001 - Measure Harness Drift" in text
    assert "- **ID**: `0001_measure_harness_drift`" in text


def test_contract_command_reports_invalid_slug(tmp_path) -> None:
    result = CliRunner().invoke(
        main,
        [
            "contract",
            "--directory",
            str(tmp_path),
            "--slug",
            "Bad Slug",
            "Title",
        ],
    )

    assert result.exit_code != 0
    assert "Invalid contract input" in result.output
    assert "lowercase letters" in result.output


def test_unknown_command_is_rejected() -> None:
    result = CliRunner().invoke(main, ["unknown-command"])

    assert result.exit_code != 0
    assert "No such command" in result.output
