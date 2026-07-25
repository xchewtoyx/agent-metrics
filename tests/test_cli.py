import json

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


@pytest.mark.parametrize("command", ["roll"])
def test_skeleton_command_fails_clearly(command: str) -> None:
    """Negative case: command stubs must fail honestly until implemented."""
    args = [command]

    result = CliRunner().invoke(main, args)

    assert result.exit_code != 0
    assert "not implemented yet" in result.output


def test_audit_command_reports_contract_counts_as_json(tmp_path) -> None:
    runner = CliRunner()
    contract_result = runner.invoke(
        main,
        ["contract", "--directory", str(tmp_path), "Measure Harness Drift"],
    )
    settle_result = runner.invoke(
        main,
        [
            "settle",
            "--directory",
            str(tmp_path),
            "--verdict",
            "KEEP",
            "--evidence",
            "Narrow tests passed.",
            "0001_measure_harness_drift",
        ],
    )

    result = runner.invoke(main, ["audit", "--directory", str(tmp_path)])

    assert contract_result.exit_code == 0
    assert settle_result.exit_code == 0
    assert result.exit_code == 0
    assert json.loads(result.output) == {
        "contracts_dir": str(tmp_path / ".agent-metrics" / "contracts"),
        "contract_files": 1,
        "settled_contracts": 1,
        "unsettled_contracts": 0,
        "malformed_contract_files": 0,
        "ignored_markdown_files": 0,
        "limitation": (
            "Audits .agent-metrics/contracts/*.md only; does not infer all git "
            "changes."
        ),
    }


def test_audit_command_reports_missing_contract_directory(tmp_path) -> None:
    result = CliRunner().invoke(main, ["audit", "--directory", str(tmp_path)])

    assert result.exit_code == 0
    assert json.loads(result.output)["contract_files"] == 0


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


def test_settle_command_records_verdict_and_evidence(tmp_path) -> None:
    contract_result = CliRunner().invoke(
        main,
        ["contract", "--directory", str(tmp_path), "Measure Harness Drift"],
    )
    contract_path = (
        tmp_path / ".agent-metrics" / "contracts" / "0001_measure_harness_drift.md"
    )

    result = CliRunner().invoke(
        main,
        [
            "settle",
            "--directory",
            str(tmp_path),
            "--verdict",
            "KEEP",
            "--evidence",
            "Narrow tests passed.",
            "0001_measure_harness_drift",
        ],
    )

    assert contract_result.exit_code == 0
    assert result.exit_code == 0
    assert result.output.strip().endswith(
        ".agent-metrics/contracts/0001_measure_harness_drift.md"
    )
    text = contract_path.read_text(encoding="utf-8")
    assert "## Settlement" in text
    assert "- **Verdict**: KEEP" in text
    assert "Narrow tests passed." in text


def test_settle_command_reports_missing_contract(tmp_path) -> None:
    result = CliRunner().invoke(
        main,
        [
            "settle",
            "--directory",
            str(tmp_path),
            "--verdict",
            "KEEP",
            "--evidence",
            "No contract exists.",
            "0001_missing_contract",
        ],
    )

    assert result.exit_code != 0
    assert "Invalid settlement input" in result.output
    assert "does not exist" in result.output


def test_settle_command_reports_invalid_verdict(tmp_path) -> None:
    contract_result = CliRunner().invoke(
        main,
        ["contract", "--directory", str(tmp_path), "Measure Harness Drift"],
    )

    result = CliRunner().invoke(
        main,
        [
            "settle",
            "--directory",
            str(tmp_path),
            "--verdict",
            "MAYBE",
            "--evidence",
            "Ambiguous evidence.",
            "0001_measure_harness_drift",
        ],
    )

    assert contract_result.exit_code == 0
    assert result.exit_code != 0
    assert "Invalid settlement input" in result.output
    assert "KEEP, IMPROVE, or ROLLBACK" in result.output


def test_settle_command_reports_repeat_settlement(tmp_path) -> None:
    contract_result = CliRunner().invoke(
        main,
        ["contract", "--directory", str(tmp_path), "Measure Harness Drift"],
    )
    first_result = CliRunner().invoke(
        main,
        [
            "settle",
            "--directory",
            str(tmp_path),
            "--verdict",
            "KEEP",
            "--evidence",
            "First settlement.",
            "0001_measure_harness_drift",
        ],
    )

    result = CliRunner().invoke(
        main,
        [
            "settle",
            "--directory",
            str(tmp_path),
            "--verdict",
            "ROLLBACK",
            "--evidence",
            "Second settlement.",
            "0001_measure_harness_drift",
        ],
    )

    assert contract_result.exit_code == 0
    assert first_result.exit_code == 0
    assert result.exit_code != 0
    assert "Invalid settlement input" in result.output
    assert "already has a settlement" in result.output


def test_unknown_command_is_rejected() -> None:
    result = CliRunner().invoke(main, ["unknown-command"])

    assert result.exit_code != 0
    assert "No such command" in result.output
