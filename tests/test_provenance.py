"""Tests for the provenance envelope and versioned JSONL schemas."""

from __future__ import annotations

import os
import subprocess
from unittest.mock import patch

from agent_metrics.provenance import (
    ADVISORY,
    CI,
    DEFAULT_BUNDLE,
    DURABLE,
    EFFECTIVENESS_SCHEMA_VERSION,
    LOCAL,
    STRUCTURAL_HEALTH_SCHEMA_VERSION,
    build_effectiveness_envelope,
    build_provenance,
    classify_durability,
    detect_environment,
    effectiveness_dedupe_key,
    get_git_metadata,
    get_host,
    resolve_timestamp,
    structural_health_dedupe_key,
)


def _git_side_effect(commit: str, remote: str, branch: str, status: str) -> list:
    """Build the ordered subprocess results for a full git metadata probe."""
    return [
        subprocess.CompletedProcess(args=[], returncode=0, stdout="true\n"),
        subprocess.CompletedProcess(args=[], returncode=0, stdout=f"{commit}\n"),
        subprocess.CompletedProcess(args=[], returncode=0, stdout=f"{remote}\n"),
        subprocess.CompletedProcess(args=[], returncode=0, stdout=f"{branch}\n"),
        subprocess.CompletedProcess(args=[], returncode=0, stdout=status),
    ]


def test_get_git_metadata_dirty() -> None:
    """Git metadata reports identity and a dirty worktree."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = _git_side_effect(
            "abcd123", "https://github.com/foo/bar.git", "main", "M file.py\n"
        )

        meta = get_git_metadata(".")
        assert meta["commit"] == "abcd123"
        assert meta["remote_url"] == "https://github.com/foo/bar.git"
        assert meta["branch"] == "main"
        assert meta["dirty"] is True


def test_get_git_metadata_clean() -> None:
    """Git metadata reports a clean worktree when status is empty."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = _git_side_effect(
            "abcd123", "https://github.com/foo/bar.git", "feature", ""
        )

        meta = get_git_metadata(".")
        assert meta["branch"] == "feature"
        assert meta["dirty"] is False


def test_get_git_metadata_subprocess_error() -> None:
    """Git metadata degrades gracefully on subprocess errors."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.SubprocessError("git error")

        meta = get_git_metadata(".")
        assert meta == {
            "commit": None,
            "remote_url": None,
            "branch": None,
            "dirty": True,
        }


def test_get_git_metadata_git_not_installed() -> None:
    """Git metadata degrades gracefully when git is missing."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("git not found")

        meta = get_git_metadata(".")
        assert meta["commit"] is None
        assert meta["dirty"] is True


def test_get_git_metadata_command_failures() -> None:
    """Non-zero git subcommands leave identity fields as None."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="true\n"),
            subprocess.CompletedProcess(args=[], returncode=1, stdout=""),
            subprocess.CompletedProcess(args=[], returncode=1, stdout=""),
            subprocess.CompletedProcess(args=[], returncode=1, stdout=""),
            subprocess.CompletedProcess(args=[], returncode=1, stdout=""),
        ]

        meta = get_git_metadata(".")
        assert meta["commit"] is None
        assert meta["remote_url"] is None
        assert meta["branch"] is None
        assert meta["dirty"] is True


def test_get_git_metadata_not_in_work_tree() -> None:
    """A path outside a work tree yields empty identity."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = [
            subprocess.CompletedProcess(args=[], returncode=0, stdout="false\n"),
        ]

        meta = get_git_metadata(".")
        assert meta["commit"] is None
        assert meta["branch"] is None
        assert meta["dirty"] is True


def test_get_host_success() -> None:
    """get_host returns the resolved host name."""
    with patch("socket.gethostname", return_value="build-box"):
        assert get_host() == "build-box"


def test_get_host_fallback() -> None:
    """get_host falls back to 'unknown' when resolution fails."""
    with patch("socket.gethostname", side_effect=OSError("no name")):
        assert get_host() == "unknown"
    with patch("socket.gethostname", return_value=""):
        assert get_host() == "unknown"


def test_detect_environment() -> None:
    """A truthy CI flag selects the ci environment; otherwise local."""
    assert detect_environment({"CI": "true"}) == CI
    assert detect_environment({"CI": "1"}) == CI
    assert detect_environment({"CI": "false"}) == LOCAL
    assert detect_environment({"CI": ""}) == LOCAL
    assert detect_environment({}) == LOCAL


def test_detect_environment_default_reads_os_environ() -> None:
    """detect_environment falls back to os.environ when no mapping is given."""
    with patch.dict(os.environ, {"CI": "true"}):
        assert detect_environment() == CI


def test_classify_durability() -> None:
    """Only clean commits measured by CI are durable."""
    assert classify_durability(dirty=False, environment=CI) == DURABLE
    assert classify_durability(dirty=True, environment=CI) == ADVISORY
    assert classify_durability(dirty=False, environment=LOCAL) == ADVISORY
    assert classify_durability(dirty=True, environment=LOCAL) == ADVISORY


def test_resolve_timestamp_source_date_epoch() -> None:
    """resolve_timestamp honors a valid SOURCE_DATE_EPOCH."""
    with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": "1234567890"}):
        assert resolve_timestamp() == "2009-02-13T23:31:30Z"


def test_resolve_timestamp_ignores_invalid_epoch() -> None:
    """resolve_timestamp ignores unparseable or out-of-range epochs."""
    for value in ("invalid", str(2**63), str(2**62)):
        with patch.dict(os.environ, {"SOURCE_DATE_EPOCH": value}):
            assert resolve_timestamp().endswith("Z")


def test_build_provenance_fields() -> None:
    """build_provenance assembles every required envelope field."""
    git_meta = {
        "commit": "cafe",
        "remote_url": "https://github.com/foo/bar.git",
        "branch": "main",
        "dirty": False,
    }
    with (
        patch("agent_metrics.provenance.get_git_metadata", return_value=git_meta),
        patch("agent_metrics.provenance.get_host", return_value="ci-runner"),
        patch("agent_metrics.provenance.detect_environment", return_value=CI),
        patch(
            "agent_metrics.provenance.resolve_timestamp",
            return_value="2026-07-18T00:00:00Z",
        ),
    ):
        record = build_provenance(
            STRUCTURAL_HEALTH_SCHEMA_VERSION,
            bundle="okf-core",
            tool_version="0.2.0",
        )

    assert record == {
        "schema_version": STRUCTURAL_HEALTH_SCHEMA_VERSION,
        "remote_url": "https://github.com/foo/bar.git",
        "commit": "cafe",
        "branch": "main",
        "dirty": False,
        "bundle": "okf-core",
        "host": "ci-runner",
        "environment": CI,
        "durability": DURABLE,
        "timestamp": "2026-07-18T00:00:00Z",
        "tool_version": "0.2.0",
    }


def test_build_provenance_defaults() -> None:
    """build_provenance uses the default bundle when none is supplied."""
    git_meta = {
        "commit": "cafe",
        "remote_url": "u",
        "branch": "b",
        "dirty": True,
    }
    with (
        patch("agent_metrics.provenance.get_git_metadata", return_value=git_meta),
        patch("agent_metrics.provenance.get_host", return_value="host"),
        patch("agent_metrics.provenance.detect_environment", return_value=LOCAL),
        patch("agent_metrics.provenance.resolve_timestamp", return_value="t"),
    ):
        record = build_provenance(STRUCTURAL_HEALTH_SCHEMA_VERSION)

    assert record["bundle"] == DEFAULT_BUNDLE
    assert record["durability"] == ADVISORY


def test_build_effectiveness_envelope() -> None:
    """Effectiveness records carry provenance plus experiment coordinates."""
    git_meta = {
        "commit": "cafe",
        "remote_url": "https://github.com/foo/bar.git",
        "branch": "main",
        "dirty": False,
    }
    with (
        patch("agent_metrics.provenance.get_git_metadata", return_value=git_meta),
        patch("agent_metrics.provenance.get_host", return_value="ci-runner"),
        patch("agent_metrics.provenance.detect_environment", return_value=CI),
        patch("agent_metrics.provenance.resolve_timestamp", return_value="t"),
    ):
        record = build_effectiveness_envelope(
            model="claude",
            harness_version="1.4.0",
            task_set="swe-bench-lite",
            run_index=2,
            experiment_arms=["control", "treatment"],
            metrics={"solved": 41},
            bundle="okf-core",
        )

    assert record["schema_version"] == EFFECTIVENESS_SCHEMA_VERSION
    assert record["model"] == "claude"
    assert record["harness_version"] == "1.4.0"
    assert record["task_set"] == "swe-bench-lite"
    assert record["run_index"] == 2
    assert record["experiment_arms"] == ["control", "treatment"]
    assert record["metrics"] == {"solved": 41}


def test_build_effectiveness_envelope_defaults() -> None:
    """Effectiveness arms and metrics default to empty containers."""
    with (
        patch(
            "agent_metrics.provenance.build_provenance",
            return_value={"schema_version": EFFECTIVENESS_SCHEMA_VERSION},
        ),
    ):
        record = build_effectiveness_envelope(
            model="claude",
            harness_version="1.4.0",
            task_set="swe-bench-lite",
            run_index=0,
        )

    assert record["experiment_arms"] == []
    assert record["metrics"] == {}


def test_structural_health_dedupe_key_ignores_context() -> None:
    """The structural key excludes branch and host context fields."""
    base = {
        "remote_url": "https://github.com/foo/bar.git",
        "bundle": "okf-core",
        "commit": "cafe",
        "schema_version": STRUCTURAL_HEALTH_SCHEMA_VERSION,
    }
    on_ci = {**base, "branch": "main", "host": "ci"}
    on_laptop = {**base, "branch": "feature", "host": "laptop"}

    assert structural_health_dedupe_key(on_ci) == structural_health_dedupe_key(
        on_laptop
    )
    assert structural_health_dedupe_key(base) == (
        "https://github.com/foo/bar.git",
        "okf-core",
        "cafe",
        STRUCTURAL_HEALTH_SCHEMA_VERSION,
    )


def test_effectiveness_dedupe_key_separates_runs_and_arms() -> None:
    """The effectiveness key separates replays and experiment arms."""
    base = {
        "remote_url": "u",
        "bundle": "okf-core",
        "commit": "cafe",
        "schema_version": EFFECTIVENESS_SCHEMA_VERSION,
        "model": "claude",
        "harness_version": "1.4.0",
        "task_set": "swe-bench-lite",
        "run_index": 0,
        "experiment_arms": ["control"],
    }
    other_run = {**base, "run_index": 1}
    other_arm = {**base, "experiment_arms": ["treatment"]}

    assert effectiveness_dedupe_key(base) != effectiveness_dedupe_key(other_run)
    assert effectiveness_dedupe_key(base) != effectiveness_dedupe_key(other_arm)
    assert effectiveness_dedupe_key({}) == (
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        (),
    )
