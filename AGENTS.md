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
  practical beats clever.
- Prefer test-driven development for behavior changes.
- Test both positive and negative cases. A command that succeeds should prove the happy
  path; a command that rejects bad input should fail clearly and usefully.
- Optimize for maintainability before performance, then measure before tuning.

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
