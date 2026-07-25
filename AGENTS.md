# Agent Instructions

## Project Aim

`agent-metrics` is a lightweight, serverless toolkit for measuring whether changes to
agent harnesses and knowledge repos actually help. The goal is robust, efficient, and
minimal evidence collection: plain files first, clear provenance, explicit contracts,
and settled outcomes.

## Engineering Principles

- Prefer batteries over bespoke machinery. Use proven libraries and standard Python
  tooling before inventing project-specific frameworks.
- Avoid reinventing wheels. Add abstractions only when they remove real complexity or
  make evidence easier to collect and verify.
- Keep changes small and testable. The project should remain useful before it becomes
  elaborate.
- Align reviews with the Zen of Python: simple, explicit, readable, sparse, and
  practical beats clever. Remember that design is complete not when there is nothing
  more to add, but when there is nothing more to remove.
- Prefer test-driven development for behavior changes.
- Test both positive and negative cases. A command that succeeds should prove the happy
  path; a command that rejects bad input should fail clearly and usefully.
- Optimize for maintainability before performance, then measure before tuning.
- Leave the codebase cleaner than you found it (the Boy Scout Rule) by proactively
  removing any imports, variables, or functions that your changes made unused.
- Document all user-facing or behavior changes in [CHANGELOG.md](CHANGELOG.md) under the `[Unreleased]` section following [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) conventions on every pull request.

## Golden Path for a Change

For a load-bearing harness or knowledge change, follow this loop:

1. **Contract first.** Scaffold a prediction in `.agent-metrics/contracts/NNNN_slug.md` (observed failure, root cause, proposed change, predicted fixes, risks, verification, settle criteria) before load-bearing edits. Pure docs or trivial refactors can skip this.
2. **Library-first.** Put logic in a focused module under `src/agent_metrics/`, keep `cli.py` thin, and expose through `__all__` only what consumers call. Follow the naming verbs in [docs/api-conventions.md](docs/api-conventions.md).
3. **Records through provenance.** Every JSONL record uses the provenance envelope with a versioned `schema_version`; dedupe by commit, and map to OpenTelemetry only at the export boundary. See [docs/schemas.md](docs/schemas.md).
4. **Verify.** Cover positive and negative cases and assert documented guarantees (not just line coverage — see [docs/review-checklist.md](docs/review-checklist.md)). Run `python scripts/review.py` (`black`/`ruff`/`pytest`) and update `CHANGELOG.md`.
5. **Settle.** Record the outcome and verdict against the contract's settle criteria.

## Project Layout and API Design

- **Maintain the `src/` Layout:** Keep all application and library source code inside the `src/` directory. Configuration, documentation, and tests must remain strictly outside the `src/` folder to prevent import path pollution and maintain a clean packaging boundary.
- **Thin CLI & Reusable Library API:** The CLI entrypoint (`src/agent_metrics/cli.py`) must remain a lightweight argument parsing and presentation layer. All core business logic must be implemented as clean, library-first functions inside `src/agent_metrics/` and exposed programmatically through the package root (`src/agent_metrics/__init__.py`).
- **Mirrored Testing Structure:** All test modules must reside in the top-level `tests/` directory, matching the file layout, module structure, and naming conventions of the source package to ensure clean organization and complete coverage.
- **Domain Modularity & Separation of Concerns:** As the library grows, divide business logic into highly cohesive, single-responsibility submodules (e.g., `src/agent_metrics/health.py`, `src/agent_metrics/contracts.py`). Avoid adding unrelated logic to existing submodules or creating monolithic files.
- **Strict API Encapsulation:** Treat the package-level `src/agent_metrics/__init__.py` as the strict public gateway (`__all__`). Programmatic entry points, helpers, or modules not exposed in `__all__` (or prefixed with a leading underscore) are considered private/internal implementation details and can be refactored at any time.
- **Explicit Interfaces:** Public API functions must use Python type hints, document their behavior clearly with docstrings, and return standard structures (like dictionaries, lists, or dataclasses) rather than relying on mutable global states or CLI-specific constructs.
- **Decoupled Exception Hierarchy:** Raise custom exception classes inheriting from a base library exception (like `AgentMetricsError`) for expected domain-level validation and runtime failures. Decouple error raising from CLI presentation by letting the CLI layer map these custom exceptions to user-facing messages.

## Testing Standard

- **Decompose tests.** One behavior per test function. A test name that
  needs "and" to describe it is a signal to split it.
- **Negative paths are mandatory.** Every new branch, guard, or validation
  path needs a test that proves it rejects bad input clearly — not just a
  test that proves the happy path works. See [docs/review-checklist.md](docs/review-checklist.md).
- **Parametrize input families.** Use `pytest.mark.parametrize` for a family
  of similar inputs instead of copy-pasted near-duplicate test functions;
  keep parametrize IDs readable.
- **Assert guarantees, not just coverage.** 100% line coverage is necessary
  but not sufficient — every defect found in review so far shipped with full
  coverage. Documented guarantees (never raises, graceful degradation,
  determinism, single-source version) get a test that pins the guarantee.
  See [tests/test_invariants.py](tests/test_invariants.py).

## Complexity & Quality Budget

- **Cyclomatic complexity ceiling.** `ruff`'s `C90` rule enforces
  `max-complexity = 8` (see `pyproject.toml`). A function that hits the
  ceiling gets decomposed into smaller, named functions — it does not get a
  `# noqa`.
- **Thin CLI/handler layers.** `cli.py` stays a thin argument/option parsing
  and presentation layer; all branching and business logic lives in library
  modules under `src/agent_metrics/` (see Project Layout, below).
- **A comment introducing a block is a function name in disguise.** If a
  comment exists to narrate what a chunk of code is about to do ("# now
  validate the input", "# build the envelope"), extract that chunk into a
  well-named helper instead of narrating it in place.

## Docs Updated in the Same Commit

Any user-facing or behavior change — a new or changed CLI option, a public
API addition, a JSONL schema change, a new error type — updates its doc in
the *same* commit: the relevant `docs/*.md` page, `README.md` if it affects
usage or install, and `CHANGELOG.md`'s `[Unreleased]` section (see below). A
PR that changes behavior without a matching docs diff fails review.

## Delivery Rules

- **One issue, one fresh branch, one PR.** Branch from the latest `main`;
  never reuse a branch across issues.
- **PRs only.** Nothing lands on `main` by direct push.
- **No agent self-merge.** An agent (including the milestone-delivery
  supervisor) opens and updates PRs but never merges its own PR — merging is
  always a human action.
- **No force-push.** Push follow-up commits; do not rewrite history on an
  open PR.
- **Reference the issue.** A PR's description includes `Closes #N` for the
  issue it resolves, and follows the repo's PR template if one exists (none
  as of this writing — until one is added, use a Summary / Test plan shape
  consistent with [docs/review-checklist.md](docs/review-checklist.md)'s
  gates).

## Local Workflow

Prefer creating a project-local virtual environment at `.venv/`:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run these checks before publishing changes:

```bash
black .
ruff check .
pytest
```

The test suite runs with coverage enabled through `pyproject.toml`.

## Review Focus

Reviews should ask:

- Is this the smallest useful change?
- Is the behavior covered by tests, including failure cases?
- Is there an existing library or standard tool that should be used instead?
- Does the implementation keep evidence reproducible and provenance explicit?
- Is the code easy to read without relying on hidden context?
- Does this change update [CHANGELOG.md](CHANGELOG.md) in the `[Unreleased]` section using Keep a Changelog conventions?

Apply the repo-specific gates in [docs/review-checklist.md](docs/review-checklist.md).

## Where to Look

Keep this file lean — it is always in context. Detailed reference lives in `docs/`
and is loaded on demand:

- [docs/schemas.md](docs/schemas.md) — JSONL schemas, provenance envelope, and OpenTelemetry mapping.
- [docs/api-conventions.md](docs/api-conventions.md) — naming verbs and public-API rules.
- [docs/review-checklist.md](docs/review-checklist.md) — repo-specific review gates.
- [docs/releasing.md](docs/releasing.md) — versioning policy and the tag/release/publish flow.
- `.agent-metrics/contracts/` — change contracts and their settle records.
- [docs/agents/](docs/agents/) — the four narrow milestone-delivery roles
  (`planner`, `implementor`, `reviewer`, `approver`): inputs, constraints,
  and exact output shape for each.
- [docs/workflows/milestone-delivery.md](docs/workflows/milestone-delivery.md)
  — the supervisor loop that drives a GitHub milestone's issues through
  plan → implement → review → approve → PR → human merge, one at a time.
  Platform-specific stubs (`.claude/`, `.cursor/`, `.github/copilot-instructions.md`,
  `CLAUDE.md`) all defer to this file and to `docs/agents/`; edit those, not
  the stubs, when the loop's behavior changes.

When adding guidance, prefer a new or existing `docs/` page linked here over
growing this file.
