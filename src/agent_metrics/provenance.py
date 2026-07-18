"""Versioned JSONL schemas and the shared provenance envelope.

Every agent-metrics JSONL record carries a provenance envelope. The remote
repository URL and commit SHA are the *durable identity* used to deduplicate a
bundle across local checkouts, hosts, branches, and CI runs. Branch, host, and
environment are recorded as *context* only, so the same bundle at the same
commit dedupes cleanly regardless of where it was measured.

Two record shapes build on the shared envelope:

* **Structural health** records are cheap, mechanical snapshots. They dedupe on
  ``(repo, bundle, commit, schema_version)``.
* **Effectiveness** records capture judgment-heavy A/B replay outcomes. They add
  the experiment coordinates (model, harness version, task set, run index, and
  experiment arms) so replays and arms stay distinct.

Records are also classified by *durability*: ``durable`` records come from a
clean commit measured by CI (for example on merge) and are the settled evidence
of record; ``advisory`` records come from local or dirty runs and are
informational only.
"""

from __future__ import annotations

import contextlib
import os
import socket
import subprocess
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from typing import Any

# Versioned schema identifiers. Bump the trailing version when a record's shape
# changes in a way that consumers must distinguish.
STRUCTURAL_HEALTH_SCHEMA_VERSION = "agent-metrics/structural-health/v1"
EFFECTIVENESS_SCHEMA_VERSION = "agent-metrics/effectiveness/v1"

# Default bundle identifier when a caller does not name the measured bundle.
DEFAULT_BUNDLE = "default"

# Durability classes.
DURABLE = "durable"  # clean commit measured by CI (for example on merge)
ADVISORY = "advisory"  # local or dirty run; informational only

# Execution environments.
CI = "ci"
LOCAL = "local"


def _git_value(abs_path: str, args: list[str]) -> str | None:
    """Return the stripped stdout of a git command, or None on any failure."""
    res = subprocess.run(
        ["git", *args],
        cwd=abs_path,
        capture_output=True,
        text=True,
    )
    if res.returncode == 0:
        return res.stdout.strip() or None
    return None


def get_git_metadata(repo_path: str = ".") -> dict[str, Any]:
    """Resolve the git identity of a repository path.

    Returns a dictionary with keys ``commit``, ``remote_url``, ``branch``, and
    ``dirty``. Missing values fall back to ``None`` (identity) or ``True``
    (``dirty``) so that non-git or partial environments are never treated as a
    clean, durable commit.
    """
    commit = None
    remote_url = None
    branch = None
    dirty = True

    abs_path = os.path.abspath(repo_path)

    try:
        inside = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=abs_path,
            capture_output=True,
            text=True,
            check=True,
        )
        if inside.stdout.strip() == "true":
            commit = _git_value(abs_path, ["rev-parse", "HEAD"])
            remote_url = _git_value(abs_path, ["config", "--get", "remote.origin.url"])
            branch = _git_value(abs_path, ["rev-parse", "--abbrev-ref", "HEAD"])

            status = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=abs_path,
                capture_output=True,
                text=True,
            )
            if status.returncode == 0:
                dirty = bool(status.stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError):
        # Gracefully handle non-git environments.
        pass

    return {
        "commit": commit,
        "remote_url": remote_url,
        "branch": branch,
        "dirty": dirty,
    }


def get_host() -> str:
    """Return the current host name, or ``"unknown"`` if it cannot be resolved."""
    try:
        return socket.gethostname() or "unknown"
    except OSError:
        return "unknown"


def _is_truthy(value: str | None) -> bool:
    """Interpret a CI-style environment flag as a boolean."""
    if value is None:
        return False
    return value.strip().lower() not in ("", "0", "false", "no")


def detect_environment(env: Mapping[str, str] | None = None) -> str:
    """Return ``"ci"`` when a CI environment flag is set, otherwise ``"local"``.

    The ``CI`` variable is set to a truthy value by every major CI provider
    (GitHub Actions, GitLab CI, CircleCI, Travis), which is a good enough signal
    to separate durable CI evidence from advisory local runs.
    """
    environ = os.environ if env is None else env
    return CI if _is_truthy(environ.get("CI")) else LOCAL


def classify_durability(dirty: bool, environment: str) -> str:
    """Classify a record as ``durable`` or ``advisory``.

    A record is durable only when it measures a clean commit inside a CI
    environment; everything else (local runs, dirty worktrees) is advisory.
    """
    if environment == CI and not dirty:
        return DURABLE
    return ADVISORY


def resolve_timestamp() -> str:
    """Return an ISO 8601 UTC timestamp.

    Honors ``SOURCE_DATE_EPOCH`` for reproducible builds, ignoring values that
    are non-integer or out of the platform's representable range.
    """
    source_date_epoch = os.environ.get("SOURCE_DATE_EPOCH")
    moment = datetime.now(UTC)
    if source_date_epoch is not None:
        with contextlib.suppress(ValueError, OverflowError, OSError):
            moment = datetime.fromtimestamp(int(source_date_epoch), tz=UTC)
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def build_provenance(
    schema_version: str,
    *,
    bundle: str = DEFAULT_BUNDLE,
    directory: str = ".",
    tool_version: str = "0.1.0",
) -> dict[str, Any]:
    """Build the provenance envelope shared by every JSONL record.

    Durable identity is ``remote_url`` and ``commit``; ``branch``, ``host``, and
    ``environment`` are context. ``durability`` distinguishes durable CI-on-merge
    evidence from advisory local runs.
    """
    git_meta = get_git_metadata(directory)
    environment = detect_environment()
    return {
        "schema_version": schema_version,
        "remote_url": git_meta["remote_url"],
        "commit": git_meta["commit"],
        "branch": git_meta["branch"],
        "dirty": git_meta["dirty"],
        "bundle": bundle,
        "host": get_host(),
        "environment": environment,
        "durability": classify_durability(git_meta["dirty"], environment),
        "timestamp": resolve_timestamp(),
        "tool_version": tool_version,
    }


def build_effectiveness_envelope(
    *,
    model: str,
    harness_version: str,
    task_set: str,
    run_index: int,
    experiment_arms: Sequence[str] | None = None,
    metrics: Mapping[str, Any] | None = None,
    bundle: str = DEFAULT_BUNDLE,
    directory: str = ".",
    tool_version: str = "0.1.0",
) -> dict[str, Any]:
    """Build an effectiveness (A/B replay) record.

    Wraps the shared provenance envelope and adds the experiment coordinates
    needed to compare a harness or knowledge change across arms and replays.
    """
    record = build_provenance(
        EFFECTIVENESS_SCHEMA_VERSION,
        bundle=bundle,
        directory=directory,
        tool_version=tool_version,
    )
    record.update(
        {
            "model": model,
            "harness_version": harness_version,
            "task_set": task_set,
            "run_index": run_index,
            "experiment_arms": list(experiment_arms or []),
            "metrics": dict(metrics or {}),
        }
    )
    return record


def structural_health_dedupe_key(record: Mapping[str, Any]) -> tuple[Any, ...]:
    """Deduplication identity for a structural health record.

    ``(repo, bundle, commit, schema_version)``. Branch and host are context and
    deliberately excluded so the same bundle at the same commit dedupes cleanly
    across checkouts, hosts, and branches.
    """
    return (
        record.get("remote_url"),
        record.get("bundle"),
        record.get("commit"),
        record.get("schema_version"),
    )


def effectiveness_dedupe_key(record: Mapping[str, Any]) -> tuple[Any, ...]:
    """Deduplication identity for an effectiveness record.

    Extends the structural key with the experiment coordinates so replays and
    experiment arms stay distinct.
    """
    return (
        record.get("remote_url"),
        record.get("bundle"),
        record.get("commit"),
        record.get("schema_version"),
        record.get("model"),
        record.get("harness_version"),
        record.get("task_set"),
        record.get("run_index"),
        tuple(record.get("experiment_arms") or ()),
    )
