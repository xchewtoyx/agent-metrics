"""Tests for markdown contract scaffolding."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pytest

from agent_metrics.contracts import (
    ContractAlreadySettledError,
    ContractCollisionError,
    ContractNameError,
    ContractNotFoundError,
    ContractVerdictError,
    scaffold_contract,
    settle_contract,
)

if TYPE_CHECKING:
    from pathlib import Path


def test_scaffold_contract_creates_next_numbered_template(tmp_path: Path) -> None:
    contract_dir = tmp_path / ".agent-metrics" / "contracts"
    contract_dir.mkdir(parents=True)
    (contract_dir / "0001_initial.md").write_text("existing", encoding="utf-8")

    scaffold = scaffold_contract(
        "Contract Command",
        directory=tmp_path,
        created_on=date(2026, 7, 22),
    )

    assert scaffold.contract_id == "0002_contract_command"
    assert scaffold.number == 2
    assert scaffold.slug == "contract_command"
    assert scaffold.path == contract_dir / "0002_contract_command.md"

    text = scaffold.path.read_text(encoding="utf-8")
    assert "# Change Contract: 0002 - Contract Command" in text
    assert "- **ID**: `0002_contract_command`" in text
    assert "- **Created**: 2026-07-22" in text
    assert "## Observed Failure Evidence" in text
    assert "## Settle Criteria (Evidence for Verdict)" in text


def test_scaffold_contract_uses_explicit_slug_and_number(tmp_path: Path) -> None:
    scaffold = scaffold_contract(
        "Human Friendly Title",
        directory=tmp_path,
        slug="custom_contract",
        number=42,
        created_on=date(2026, 7, 22),
    )

    assert scaffold.contract_id == "0042_custom_contract"
    assert scaffold.path.name == "0042_custom_contract.md"


@pytest.mark.parametrize(
    ("title", "slug", "message"),
    [
        ("   ", None, "title cannot be empty"),
        ("Valid title", "Bad Slug", "lowercase letters"),
        ("!!!", None, "lowercase letters"),
    ],
)
def test_scaffold_contract_rejects_invalid_names(
    tmp_path: Path,
    title: str,
    slug: str | None,
    message: str,
) -> None:
    with pytest.raises(ContractNameError, match=message):
        scaffold_contract(title, directory=tmp_path, slug=slug)


@pytest.mark.parametrize("number", [0, 10000])
def test_scaffold_contract_rejects_invalid_number(
    tmp_path: Path,
    number: int,
) -> None:
    with pytest.raises(ContractNameError, match="between 1 and 9999"):
        scaffold_contract("Title", directory=tmp_path, number=number)


def test_scaffold_contract_rejects_number_collision(tmp_path: Path) -> None:
    contract_dir = tmp_path / ".agent-metrics" / "contracts"
    contract_dir.mkdir(parents=True)
    (contract_dir / "0007_existing.md").write_text("existing", encoding="utf-8")

    with pytest.raises(ContractCollisionError, match="number 0007 already exists"):
        scaffold_contract("New Topic", directory=tmp_path, number=7)


def test_scaffold_contract_rejects_slug_collision(tmp_path: Path) -> None:
    contract_dir = tmp_path / ".agent-metrics" / "contracts"
    contract_dir.mkdir(parents=True)
    (contract_dir / "0007_existing_topic.md").write_text(
        "existing",
        encoding="utf-8",
    )

    with pytest.raises(ContractCollisionError, match="slug 'existing_topic'"):
        scaffold_contract("Existing Topic", directory=tmp_path)


def test_scaffold_contract_ignores_non_contract_markdown_names(tmp_path: Path) -> None:
    contract_dir = tmp_path / ".agent-metrics" / "contracts"
    contract_dir.mkdir(parents=True)
    (contract_dir / "notes.md").write_text("not a contract", encoding="utf-8")

    scaffold = scaffold_contract("Useful Change", directory=tmp_path)

    assert scaffold.path.name == "0001_useful_change.md"


def test_settle_contract_appends_settlement_without_rewriting_body(
    tmp_path: Path,
) -> None:
    scaffold = scaffold_contract(
        "Useful Change",
        directory=tmp_path,
        created_on=date(2026, 7, 22),
    )
    original_text = scaffold.path.read_text(encoding="utf-8")

    settlement = settle_contract(
        scaffold.contract_id,
        directory=tmp_path,
        verdict="keep",
        evidence="Narrow tests pass and the CLI records the settlement.",
        settled_on=date(2026, 7, 23),
    )

    assert settlement.path == scaffold.path
    assert settlement.contract_id == scaffold.contract_id
    assert settlement.verdict == "KEEP"
    assert (
        settlement.evidence == "Narrow tests pass and the CLI records the settlement."
    )

    text = scaffold.path.read_text(encoding="utf-8")
    assert text.startswith(original_text)
    assert text.count("## Settlement") == 1
    assert "- **Settled**: 2026-07-23" in text
    assert "- **Verdict**: KEEP" in text
    assert "### Evidence" in text
    assert "Narrow tests pass and the CLI records the settlement." in text


def test_settle_contract_accepts_contract_filename(tmp_path: Path) -> None:
    scaffold = scaffold_contract("Useful Change", directory=tmp_path)

    settlement = settle_contract(
        scaffold.path.name,
        directory=tmp_path,
        verdict="IMPROVE",
        evidence="Works, but future file input would help.",
    )

    assert settlement.path == scaffold.path
    assert "- **Verdict**: IMPROVE" in scaffold.path.read_text(encoding="utf-8")


def test_settle_contract_rejects_missing_contract(tmp_path: Path) -> None:
    with pytest.raises(ContractNotFoundError, match="does not exist"):
        settle_contract(
            "0001_missing_contract",
            directory=tmp_path,
            verdict="KEEP",
            evidence="No file exists.",
        )


def test_settle_contract_rejects_invalid_verdict(tmp_path: Path) -> None:
    scaffold = scaffold_contract("Useful Change", directory=tmp_path)

    with pytest.raises(ContractVerdictError, match="KEEP, IMPROVE, or ROLLBACK"):
        settle_contract(
            scaffold.contract_id,
            directory=tmp_path,
            verdict="MAYBE",
            evidence="Ambiguous verdict.",
        )


def test_settle_contract_rejects_empty_evidence(tmp_path: Path) -> None:
    scaffold = scaffold_contract("Useful Change", directory=tmp_path)

    with pytest.raises(ContractVerdictError, match="evidence cannot be empty"):
        settle_contract(
            scaffold.contract_id,
            directory=tmp_path,
            verdict="KEEP",
            evidence="   ",
        )


def test_settle_contract_rejects_repeat_settlement(tmp_path: Path) -> None:
    scaffold = scaffold_contract("Useful Change", directory=tmp_path)
    settle_contract(
        scaffold.contract_id,
        directory=tmp_path,
        verdict="KEEP",
        evidence="First settlement.",
    )

    with pytest.raises(ContractAlreadySettledError, match="already has"):
        settle_contract(
            scaffold.contract_id,
            directory=tmp_path,
            verdict="ROLLBACK",
            evidence="Second settlement should not overwrite evidence.",
        )
