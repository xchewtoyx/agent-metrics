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
    append_health_record,
    create_health_envelope,
    get_git_metadata,
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
