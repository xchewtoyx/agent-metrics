"""Tests for health snapshot functionality and CLI command."""

from __future__ import annotations

import json
import os
import subprocess
from typing import TYPE_CHECKING
from unittest.mock import patch

from click.testing import CliRunner

from agent_metrics.cli import main
from agent_metrics.health import (
    AgentMetricsError,
    append_health_record,
    capture_health,
    create_health_envelope,
    get_git_metadata,
    load_metrics,
    parse_metric_value,
    parse_metrics_definitions,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_get_git_metadata_success() -> None:
    """Test git metadata extraction when git commands succeed."""
    with patch("subprocess.run") as mock_run:
        # Mock git responses
        # 1. is-inside-work-tree -> "true"
        # 2. HEAD commit -> "abcd123"
        # 3. Remote origin -> "https://github.com/foo/bar.git"
        # 4. Git status -> "M file.py" (dirty)
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="true\n"),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="abcd123\n"),
            subprocess.CompletedProcess(
                args=[], returncode=0, stdout="https://github.com/foo/bar.git\n"
            ),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="M file.py\n"),
        ]

        meta = get_git_metadata(".")
        assert meta["commit"] == "abcd123"
        assert meta["remote_url"] == "https://github.com/foo/bar.git"
        assert meta["dirty"] is True
        assert meta["durable"] is False


def test_get_git_metadata_clean() -> None:
    """Test git metadata extraction when worktree is clean."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="true\n"),
            subprocess.CompletedProcess(args=[], returncode=0, stdout="abcd123\n"),
            subprocess.CompletedProcess(
                args=[], returncode=0, stdout="https://github.com/foo/bar.git\n"
            ),
            subprocess.CompletedProcess(args=[], returncode=0, stdout=""),
        ]

        meta = get_git_metadata(".")
        assert meta["dirty"] is False
        assert meta["durable"] is True


def test_get_git_metadata_failures() -> None:
    """Test git metadata behaves gracefully on subprocess or command failures."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.SubprocessError("git error")

        meta = get_git_metadata(".")
        assert meta["commit"] is None
        assert meta["remote_url"] is None
        assert meta["dirty"] is True
        assert meta["durable"] is False


def test_get_git_metadata_filenotfound() -> None:
    """Test git metadata behaves gracefully when git is not installed."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("git not found")

        meta = get_git_metadata(".")
        assert meta["commit"] is None
        assert meta["remote_url"] is None
        assert meta["dirty"] is True
        assert meta["durable"] is False


def test_create_health_envelope() -> None:
    """Test the envelope structure and key types."""
    with patch("agent_metrics.health.get_git_metadata") as mock_git:
        mock_git.return_value = {
            "commit": "123456",
            "remote_url": "https://remote.git",
            "dirty": False,
            "durable": True,
        }

        metrics = {"tests": 10, "coverage": 95.5, "status": "ok"}
        envelope = create_health_envelope(metrics, ".", "0.2.0")

        assert "timestamp" in envelope
        assert envelope["commit"] == "123456"
        assert envelope["remote_url"] == "https://remote.git"
        assert envelope["dirty"] is False
        assert envelope["durable"] is True
        assert envelope["tool_version"] == "0.2.0"
        assert envelope["metrics"] == metrics


def test_append_health_record(tmp_path: Path) -> None:
    """Verify appending a health record creates directories and correct JSONL lines."""
    dir_str = str(tmp_path)
    record1 = {"id": 1, "metrics": {"val": 10}}
    record2 = {"id": 2, "metrics": {"val": 20}}

    file_path = append_health_record(dir_str, record1)
    append_health_record(dir_str, record2)

    assert os.path.exists(file_path)
    assert file_path.endswith(os.path.join(".agent-metrics", "health.jsonl"))

    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == 2
    assert json.loads(lines[0]) == record1
    assert json.loads(lines[1]) == record2


def test_cli_health_empty() -> None:
    """CLI health with no parameters should output valid empty metrics JSON."""
    result = CliRunner().invoke(main, ["health"])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert "metrics" in data
    assert data["metrics"] == {}


def test_cli_health_metrics_parsing() -> None:
    """CLI health handles explicit --metric KEY=VALUE inputs and value type casting."""
    result = CliRunner().invoke(
        main,
        [
            "health",
            "--metric",
            "tests=42",
            "-m",
            "failures=0",
            "-m",
            "coverage=99.5",
            "-m",
            "status=success",
        ],
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    metrics = data["metrics"]
    assert metrics["tests"] == 42
    assert metrics["failures"] == 0
    assert metrics["coverage"] == 99.5
    assert metrics["status"] == "success"


def test_cli_health_invalid_metric_format() -> None:
    """CLI health rejects metrics without '=' or with empty keys."""
    result1 = CliRunner().invoke(main, ["health", "--metric", "invalid"])
    assert result1.exit_code != 0
    assert "must be in KEY=VALUE format" in result1.output

    result2 = CliRunner().invoke(main, ["health", "--metric", "=val"])
    assert result2.exit_code != 0
    assert "Metric key cannot be empty" in result2.output


def test_cli_health_input_file(tmp_path: Path) -> None:
    """CLI health correctly reads metrics from a JSON file."""
    metrics_data = {"coverage": 88, "linter_errors": 2}
    json_file = tmp_path / "metrics.json"
    json_file.write_text(json.dumps(metrics_data))

    result = CliRunner().invoke(main, ["health", "--input-file", str(json_file)])
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["metrics"] == metrics_data


def test_cli_health_input_file_and_metrics_merge(
    tmp_path: Path,
) -> None:
    """CLI health merges JSON file metrics and CLI key-value metrics."""
    metrics_data = {"coverage": 88, "linter_errors": 2}
    json_file = tmp_path / "metrics.json"
    json_file.write_text(json.dumps(metrics_data))

    result = CliRunner().invoke(
        main,
        [
            "health",
            "--input-file",
            str(json_file),
            "--metric",
            "coverage=95",  # overrides file metric
            "--metric",
            "tests=15",  # new metric
        ],
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["metrics"] == {"coverage": 95, "linter_errors": 2, "tests": 15}


def test_cli_health_invalid_json_file(tmp_path: Path) -> None:
    """CLI health fails gracefully when input file has invalid JSON."""
    json_file = tmp_path / "bad.json"
    json_file.write_text("{invalid")

    result = CliRunner().invoke(main, ["health", "--input-file", str(json_file)])
    assert result.exit_code != 0
    assert "Invalid JSON in metrics input" in result.output


def test_cli_health_not_object_json_file(tmp_path: Path) -> None:
    """CLI health fails when input file is a list instead of an object."""
    json_file = tmp_path / "list.json"
    json_file.write_text("[1, 2, 3]")

    result = CliRunner().invoke(main, ["health", "--input-file", str(json_file)])
    assert result.exit_code != 0
    assert "Metrics input file must be a JSON object" in result.output


def test_cli_health_stdin() -> None:
    """CLI health reads metrics JSON from stdin when input file is '-'."""
    metrics_data = {"tests": 120}
    result = CliRunner().invoke(
        main, ["health", "--input-file", "-"], input=json.dumps(metrics_data)
    )
    assert result.exit_code == 0

    data = json.loads(result.output)
    assert data["metrics"] == metrics_data


def test_cli_health_append(tmp_path: Path) -> None:
    """CLI health --append appends snapshots to .agent-metrics/health.jsonl."""
    dir_str = str(tmp_path)
    result = CliRunner().invoke(
        main,
        ["health", "--append", "--metric", "tests=5", dir_str],
    )
    assert result.exit_code == 0

    log_path = os.path.join(dir_str, ".agent-metrics", "health.jsonl")
    assert os.path.exists(log_path)

    with open(log_path, encoding="utf-8") as f:
        lines = f.readlines()

    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["metrics"] == {"tests": 5}


def test_get_git_metadata_command_failures() -> None:
    """Test git metadata when git commands return non-zero codes."""
    with patch("subprocess.run") as mock_run:
        # Mock git responses where commands fail (returncode = 1)
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="true\n"),
            subprocess.CompletedProcess(args=[], returncode=1, stdout=""),
            subprocess.CompletedProcess(args=[], returncode=1, stdout=""),
            subprocess.CompletedProcess(args=[], returncode=1, stdout=""),
        ]

        meta = get_git_metadata(".")
        assert meta["commit"] is None
        assert meta["remote_url"] is None
        assert meta["dirty"] is True
        assert meta["durable"] is False


def test_get_git_metadata_not_in_work_tree() -> None:
    """Test git metadata extraction when inside a non-work tree."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="false\n"),
        ]

        meta = get_git_metadata(".")
        assert meta["commit"] is None
        assert meta["remote_url"] is None
        assert meta["dirty"] is True
        assert meta["durable"] is False


def test_cli_health_infinite_floats() -> None:
    """CLI health rejects non-finite floats like NaN and Infinity."""
    result1 = CliRunner().invoke(main, ["health", "--metric", "val=NaN"])
    assert result1.exit_code != 0
    assert "must be a finite number" in result1.output

    result2 = CliRunner().invoke(main, ["health", "--metric", "val=Infinity"])
    assert result2.exit_code != 0
    assert "must be a finite number" in result2.output

    result3 = CliRunner().invoke(main, ["health", "--metric", "val=1e309"])
    assert result3.exit_code != 0
    assert "must be a finite number" in result3.output


def test_create_health_envelope_source_date_epoch() -> None:
    """Test create_health_envelope honors SOURCE_DATE_EPOCH."""
    with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1234567890"}):
        envelope = create_health_envelope({}, ".")
        assert envelope["timestamp"] == "2009-02-13T23:31:30Z"


def test_create_health_envelope_invalid_source_date_epoch() -> None:
    """Test create_health_envelope ignores invalid SOURCE_DATE_EPOCH."""
    with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "invalid"}):
        envelope = create_health_envelope({}, ".")
        # Should not crash and should produce a valid timestamp
        assert "timestamp" in envelope


def test_create_health_envelope_overflow_source_date_epoch() -> None:
    """Test create_health_envelope ignores SOURCE_DATE_EPOCH causing OverflowError."""
    with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": str(2**63)}):
        envelope = create_health_envelope({}, ".")
        assert "timestamp" in envelope


def test_create_health_envelope_oserror_source_date_epoch() -> None:
    """Test create_health_envelope ignores SOURCE_DATE_EPOCH that causes OSError.

    2**62 seconds is far beyond the system time_t range on 64-bit Linux and
    raises OSError('Value too large for defined data type').
    """
    with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": str(2**62)}):
        envelope = create_health_envelope({}, ".")
    assert "timestamp" in envelope


def test_cli_health_non_json_value_in_file(tmp_path: Path) -> None:
    """CLI health handles non-JSON compliant float values from files."""
    json_file = tmp_path / "metrics.json"
    json_file.write_text('{"tests": NaN}')

    result = CliRunner().invoke(main, ["health", "--input-file", str(json_file)])
    assert result.exit_code != 0
    assert "Metrics contain non-JSON values" in result.output


def test_api_load_metrics(tmp_path: Path) -> None:
    """Test load_metrics with different input types."""
    # 1. None returns empty dict
    assert load_metrics(None) == {}

    # 2. Dictionary returns copy
    d = {"test": 1}
    res = load_metrics(d)
    assert res == d
    assert res is not d

    # 3. Valid JSON filepath loading
    f = tmp_path / "valid.json"
    f.write_text('{"a": 2}')
    assert load_metrics(str(f)) == {"a": 2}

    # 4. Invalid source raises TypeError
    import pytest

    with pytest.raises(TypeError):
        load_metrics(123)

    # 5. Non-dict JSON raises AgentMetricsError
    f2 = tmp_path / "invalid.json"
    f2.write_text("[1, 2]")
    with pytest.raises(AgentMetricsError):
        load_metrics(str(f2))


def test_api_parse_metric_value() -> None:
    """Test parsing logic directly."""
    import pytest

    assert parse_metric_value("10") == 10
    assert parse_metric_value("2.5") == 2.5
    assert parse_metric_value("string") == "string"

    with pytest.raises(AgentMetricsError):
        parse_metric_value("NaN")


def test_api_parse_metrics_definitions() -> None:
    """Test definitions list parsing directly."""
    import pytest

    assert parse_metrics_definitions(["a=1", "b=foo"]) == {"a": 1, "b": "foo"}

    with pytest.raises(AgentMetricsError):
        parse_metrics_definitions(["invalid"])

    with pytest.raises(AgentMetricsError):
        parse_metrics_definitions(["=1"])


def test_api_capture_health(tmp_path: Path) -> None:
    """Test capture_health API method directly."""
    f = tmp_path / "f.json"
    f.write_text('{"from_file": 1}')

    record = capture_health(
        directory=str(tmp_path),
        metrics={"from_dict": "val"},
        input_file=str(f),
        append=True,
    )

    assert record["metrics"] == {"from_file": 1, "from_dict": "val"}
    log_path = tmp_path / ".agent-metrics" / "health.jsonl"
    assert log_path.exists()

    record2 = capture_health(
        directory=str(tmp_path),
        metrics=None,
        input_file=None,
        append=False,
    )
    assert record2["metrics"] == {}


def test_cli_health_type_error_handling() -> None:
    """Test CLI health gracefully handles TypeErrors from the API."""
    with patch("agent_metrics.health.capture_health") as mock_cap:
        mock_cap.side_effect = TypeError("Mocked TypeError")
        result = CliRunner().invoke(main, ["health"])
        assert result.exit_code != 0
        assert "Type error: Mocked TypeError" in result.output
