"""Logic for structural and codebase health snapshots."""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def get_git_metadata(repo_path: str = ".") -> dict[str, Any]:
    """Resolve git metadata for the given repository path.

    Returns a dictionary with keys: 'commit', 'remote_url', 'dirty', 'durable'.
    """
    commit = None
    remote_url = None
    dirty = True
    durable = False

    abs_path = os.path.abspath(repo_path)

    try:
        # Check if we are inside a git worktree
        res = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=abs_path,
            capture_output=True,
            text=True,
            check=True,
        )
        if res.stdout.strip() == "true":
            # Get commit
            res_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=abs_path,
                capture_output=True,
                text=True,
            )
            if res_commit.returncode == 0:
                commit = res_commit.stdout.strip()

            # Get remote URL
            res_remote = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=abs_path,
                capture_output=True,
                text=True,
            )
            if res_remote.returncode == 0:
                remote_url = res_remote.stdout.strip()

            # Get status (dirty check)
            res_status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=abs_path,
                capture_output=True,
                text=True,
            )
            if res_status.returncode == 0:
                dirty = bool(res_status.stdout.strip())
                durable = not dirty
    except (subprocess.SubprocessError, FileNotFoundError):
        # Gracefully handle non-git environments
        pass

    return {
        "commit": commit,
        "remote_url": remote_url,
        "dirty": dirty,
        "durable": durable,
    }


def create_health_envelope(
    metrics: dict[str, Any],
    directory: str = ".",
    tool_version: str = "0.1.0",
) -> dict[str, Any]:
    """Wraps user metrics in a git envelope with a current timestamp."""
    git_meta = get_git_metadata(directory)

    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    timestamp_dt = datetime.now(UTC)
    if source_date_epoch is not None:
        with contextlib.suppress(ValueError):
            timestamp_dt = datetime.fromtimestamp(int(source_date_epoch), tz=UTC)
    timestamp = timestamp_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return {
        "timestamp": timestamp,
        "commit": git_meta["commit"],
        "remote_url": git_meta["remote_url"],
        "dirty": git_meta["dirty"],
        "durable": git_meta["durable"],
        "tool_version": tool_version,
        "metrics": metrics,
    }


def append_health_record(directory: str, record: dict[str, Any]) -> str:
    """Appends a health record to the health.jsonl file under the target directory.

    Creates target directories if they do not exist. Returns the path of the file.
    """
    target_dir = os.path.join(directory, ".agent-metrics")
    os.makedirs(target_dir, exist_ok=True)
    file_path = os.path.join(target_dir, "health.jsonl")

    with open(file_path, "a", encoding="utf-8") as f:
        f.write(
            json.dumps(
                record,
                separators=(",", ":"),
                sort_keys=True,
                allow_nan=False,
            )
            + "\n"
        )

    return file_path
