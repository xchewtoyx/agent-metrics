"""Scaffold markdown change contracts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from agent_metrics.errors import AgentMetricsError

_CONTRACT_DIR = Path(".agent-metrics") / "contracts"
_CONTRACT_FILE_RE = re.compile(
    r"^(?P<number>\d{4})_(?P<slug>[a-z0-9]+(?:_[a-z0-9]+)*)\.md$"
)
_SLUG_RE = re.compile(r"^[a-z0-9]+(?:_[a-z0-9]+)*$")


class ContractError(AgentMetricsError):
    """Base exception for contract scaffold failures."""


class ContractNameError(ContractError):
    """Raised when a contract title, slug, or number is invalid."""


class ContractCollisionError(ContractError):
    """Raised when a requested contract name would collide with existing evidence."""


@dataclass(frozen=True)
class ContractScaffold:
    """Result of scaffolding a contract file."""

    path: Path
    contract_id: str
    number: int
    slug: str


def scaffold_contract(
    title: str,
    directory: str | Path = ".",
    *,
    slug: str | None = None,
    number: int | None = None,
    created_on: date | None = None,
) -> ContractScaffold:
    """Create a markdown pre-change contract scaffold.

    Filenames are deterministic for the current directory state:
    ``NNNN_slug.md`` where ``NNNN`` is either the requested number or the next
    unused numeric prefix, and ``slug`` is explicit or derived from the title.
    Existing numeric prefixes and existing slugs are treated as collisions.
    """
    clean_title = title.strip()
    if not clean_title:
        raise ContractNameError("Contract title cannot be empty.")

    contract_slug = _normalize_slug(slug) if slug is not None else _slugify(clean_title)
    contract_dir = Path(directory) / _CONTRACT_DIR
    contract_number = (
        number if number is not None else _next_contract_number(contract_dir)
    )
    if contract_number < 1 or contract_number > 9999:
        raise ContractNameError("Contract number must be between 1 and 9999.")

    _ensure_no_collision(contract_dir, contract_number, contract_slug)

    contract_id = f"{contract_number:04d}_{contract_slug}"
    path = contract_dir / f"{contract_id}.md"
    contract_dir.mkdir(parents=True, exist_ok=True)
    path.write_text(
        _render_contract_template(
            title=clean_title,
            contract_id=contract_id,
            number=contract_number,
            created_on=created_on or date.today(),
        ),
        encoding="utf-8",
    )
    return ContractScaffold(
        path=path,
        contract_id=contract_id,
        number=contract_number,
        slug=contract_slug,
    )


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
    slug = re.sub(r"_+", "_", slug)
    return _normalize_slug(slug)


def _normalize_slug(slug: str) -> str:
    clean_slug = slug.strip()
    if not _SLUG_RE.fullmatch(clean_slug):
        raise ContractNameError(
            "Contract slug must use lowercase letters, numbers, and single "
            "underscores only."
        )
    return clean_slug


def _next_contract_number(contract_dir: Path) -> int:
    numbers = [
        int(match.group("number"))
        for path in contract_dir.glob("*.md")
        if (match := _CONTRACT_FILE_RE.fullmatch(path.name))
    ]
    return max(numbers, default=0) + 1


def _ensure_no_collision(contract_dir: Path, number: int, slug: str) -> None:
    if not contract_dir.exists():
        return

    for path in contract_dir.glob("*.md"):
        match = _CONTRACT_FILE_RE.fullmatch(path.name)
        if match is None:
            continue
        if int(match.group("number")) == number:
            raise ContractCollisionError(
                f"Contract number {number:04d} already exists: {path.name}"
            )
        if match.group("slug") == slug:
            raise ContractCollisionError(
                f"Contract slug '{slug}' already exists: {path.name}"
            )


def _render_contract_template(
    *,
    title: str,
    contract_id: str,
    number: int,
    created_on: date,
) -> str:
    return f"""# Change Contract: {number:04d} - {title}

- **ID**: `{contract_id}`
- **Issue**: TODO
- **Component**: TODO
- **Created**: {created_on.isoformat()}
- **Status**: Proposed

## Observed Failure Evidence

TODO: Describe the concrete failure, friction, or missing evidence that makes
this change worth doing.

## Inferred Root Cause

TODO: Explain the likely cause behind the observed failure.

## Proposed Change

TODO: Describe the smallest useful change you plan to make before editing
load-bearing code.

## Affected Component

- TODO

## Predicted Fixes

- TODO

## Regression Risks

- TODO

## Verification Plan

1. TODO

## Settle Criteria (Evidence for Verdict)

- **KEEP**: TODO
- **IMPROVE**: TODO
- **ROLLBACK**: TODO
"""
