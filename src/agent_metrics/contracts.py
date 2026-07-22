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


class ContractNotFoundError(ContractError):
    """Raised when a requested contract file does not exist."""


class ContractAlreadySettledError(ContractError):
    """Raised when a contract already has settlement evidence."""


class ContractVerdictError(ContractError):
    """Raised when a settlement verdict or evidence value is invalid."""


@dataclass(frozen=True)
class ContractScaffold:
    """Result of scaffolding a contract file."""

    path: Path
    contract_id: str
    number: int
    slug: str


@dataclass(frozen=True)
class ContractSettlement:
    """Result of settling a contract file."""

    path: Path
    contract_id: str
    verdict: str
    evidence: str


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


def settle_contract(
    contract: str | Path,
    *,
    verdict: str,
    evidence: str,
    directory: str | Path = ".",
    settled_on: date | None = None,
) -> ContractSettlement:
    """Append settlement evidence and a validated verdict to a contract.

    ``contract`` may be a contract id (``NNNN_slug``), a contract filename, or
    a path. Settlement is append-only: the original prediction body is preserved
    and an existing settlement section is rejected by default.
    """
    contract_path = _resolve_contract_path(contract, directory)
    clean_verdict = _normalize_verdict(verdict)
    clean_evidence = evidence.strip()
    if not clean_evidence:
        raise ContractVerdictError("Settlement evidence cannot be empty.")

    original_text = contract_path.read_text(encoding="utf-8")
    if _has_settlement(original_text):
        raise ContractAlreadySettledError(
            f"Contract already has a settlement section: {contract_path}"
        )

    settlement_text = _render_settlement_section(
        verdict=clean_verdict,
        evidence=clean_evidence,
        settled_on=settled_on or date.today(),
    )
    separator = "\n" if original_text.endswith("\n") else "\n\n"
    contract_path.write_text(
        f"{original_text}{separator}{settlement_text}",
        encoding="utf-8",
    )

    return ContractSettlement(
        path=contract_path,
        contract_id=contract_path.stem,
        verdict=clean_verdict,
        evidence=clean_evidence,
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


def _normalize_verdict(verdict: str) -> str:
    clean_verdict = verdict.strip().upper()
    if clean_verdict not in {"KEEP", "IMPROVE", "ROLLBACK"}:
        raise ContractVerdictError(
            "Settlement verdict must be one of KEEP, IMPROVE, or ROLLBACK."
        )
    return clean_verdict


def _resolve_contract_path(contract: str | Path, directory: str | Path) -> Path:
    raw_path = Path(contract)
    if raw_path.suffix == ".md" and len(raw_path.parts) == 1:
        path = Path(directory) / _CONTRACT_DIR / raw_path
    elif raw_path.suffix == ".md" or len(raw_path.parts) > 1:
        path = raw_path if raw_path.is_absolute() else Path(directory) / raw_path
    else:
        contract_id = raw_path.name
        if not _CONTRACT_FILE_RE.fullmatch(f"{contract_id}.md"):
            raise ContractNameError(
                "Contract identifier must look like NNNN_lower_snake_slug."
            )
        path = Path(directory) / _CONTRACT_DIR / f"{contract_id}.md"

    if not path.is_file():
        raise ContractNotFoundError(f"Contract does not exist: {path}")
    return path


def _has_settlement(text: str) -> bool:
    return re.search(r"(?m)^## Settlement$", text) is not None


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


def _render_settlement_section(
    *,
    verdict: str,
    evidence: str,
    settled_on: date,
) -> str:
    return f"""## Settlement

- **Settled**: {settled_on.isoformat()}
- **Verdict**: {verdict}

### Evidence

{evidence}
"""
