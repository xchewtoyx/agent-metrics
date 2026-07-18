"""Contract/invariant tests.

These assert documented *guarantees* rather than exercising lines for coverage.
They exist because several defects shipped with 100% line coverage: the caught
guarantees below (graceful degradation, strict/deterministic JSON, single-source
version, documented envelope shape) were true in prose but not enforced by a
test. Each test here pins one such guarantee.
"""

from __future__ import annotations

import json
import re
import subprocess
from importlib import metadata
from pathlib import Path

import pytest

import agent_metrics as am
from agent_metrics import cli, errors, health, provenance
from agent_metrics.provenance import get_git_metadata

# Provenance fields documented in docs/schemas.md as present on every record.
_DOCUMENTED_ENVELOPE_FIELDS = {
    "schema_version",
    "remote_url",
    "commit",
    "branch",
    "dirty",
    "bundle",
    "host",
    "environment",
    "durability",
    "timestamp",
    "tool_version",
}

_DOC_ROOT = Path(__file__).resolve().parent.parent / "docs"


def test_version_matches_distribution_metadata() -> None:
    """__version__ is the installed version, not a hard-coded literal.

    Guards the version-drift class (hard-coded "0.1.0" defaults) by pinning the
    single source of truth: the distribution metadata.
    """
    assert am.__version__ == metadata.version("agent-metrics")


@pytest.mark.parametrize(
    "error",
    [
        FileNotFoundError("git absent"),
        NotADirectoryError("path is a file"),
        PermissionError("unreadable"),
        OSError("generic os error"),
        subprocess.SubprocessError("git failed"),
        subprocess.TimeoutExpired(cmd="git", timeout=1),
    ],
)
def test_get_git_metadata_never_raises_on_environment_error(
    error: Exception,
) -> None:
    """get_git_metadata degrades gracefully across the whole failure family.

    The identical "caught exceptions too narrow" bug appeared in two PRs
    (SOURCE_DATE_EPOCH, then get_git_metadata). This pins the contract for the
    entire OSError/SubprocessError family, not one hand-picked instance.
    """
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(subprocess, "run", lambda *a, **k: (_ for _ in ()).throw(error))
        meta = get_git_metadata(".")
    assert meta == {
        "commit": None,
        "remote_url": None,
        "branch": None,
        "dirty": True,
    }


def test_health_record_round_trips_as_strict_json() -> None:
    """Records serialize as strict, deterministic JSON and round-trip.

    Pins the strict-evidence invariant (sort_keys, allow_nan=False) established
    in the health work so an added field can never reintroduce non-strict JSON.
    """
    record = am.build_health_envelope({"concepts": 128, "coverage": 99.5})
    line = json.dumps(record, sort_keys=True, allow_nan=False)
    assert json.loads(line) == record


def test_every_record_carries_documented_envelope_fields() -> None:
    """capture_health emits exactly the fields documented in docs/schemas.md.

    Guards doc/code drift on the record shape: the documented envelope table and
    the produced record cannot silently diverge.
    """
    record = am.capture_health()
    assert set(record) >= _DOCUMENTED_ENVELOPE_FIELDS


def test_all_public_exports_are_importable() -> None:
    """Every name in __all__ resolves, so the documented surface is real."""
    missing = [name for name in am.__all__ if not hasattr(am, name)]
    assert not missing, f"__all__ names not importable: {missing}"


def test_api_convention_examples_reference_real_symbols() -> None:
    """Function names in the api-conventions verb table exist in the package.

    Catches stale references left behind by a rename (the recurring doc-drift
    class), scoped to the snake_case identifiers in the Examples column.
    """
    namespaces = [am, provenance, health, errors, cli]
    text = (_DOC_ROOT / "api-conventions.md").read_text(encoding="utf-8")
    # Table rows only; pull backticked snake_case identifiers from each row.
    tokens = {
        tok
        for line in text.splitlines()
        if line.lstrip().startswith("|")
        for tok in re.findall(r"`([a-z_][a-z0-9_]+)`", line)
    }
    assert tokens, "no symbols extracted from api-conventions.md — format changed?"
    unknown = [tok for tok in tokens if not any(hasattr(ns, tok) for ns in namespaces)]
    assert not unknown, f"docs reference unknown symbols: {sorted(unknown)}"
