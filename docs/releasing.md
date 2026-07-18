# Releasing

`agent-metrics` is distributed as a self-hosted [PEP 503](https://peps.python.org/pep-0503/)
simple index on GitHub Pages, built from GitHub Release assets. It is not
published to PyPI. Releases are cut by tagging a version and publishing a GitHub
Release; a workflow builds the artifacts, attaches them, and refreshes the index.

## Installation (for consumers)

```bash
pip install agent-metrics \
  --index-url https://xchewtoyx.github.io/agent-metrics/simple/ \
  --extra-index-url https://pypi.org/simple/
```

The `--extra-index-url` keeps PyPI available for dependencies. With `uv`:

```toml
[[tool.uv.index]]
url = "https://xchewtoyx.github.io/agent-metrics/simple/"
```

## Versioning policy (`tool_version`)

The package version is the `version` field in `pyproject.toml` and is the single
source of truth. `agent_metrics.__version__` and every record's `tool_version`
resolve from the installed distribution metadata, so they always match the
release. Follow [Semantic Versioning](https://semver.org/):

| Bump | When |
| ---- | ---- |
| **MAJOR** (`X.0.0`) | Backward-incompatible change: remove/rename a public API export, remove/rename/retype a JSONL field, or change deduplication semantics (which also bumps the affected `schema_version`). |
| **MINOR** (`0.X.0`) | Backward-compatible addition: new public API, new CLI command or option, or a new *optional* JSONL field. |
| **PATCH** (`0.0.X`) | Bug fixes, docs, or internal refactors with no public API or on-disk schema change. |

While the package is pre-1.0 (`0.y.z`), a MINOR bump may carry a breaking change
per SemVer's initial-development clause — but an on-disk record break must still
bump the affected `schema_version` regardless of the package version.

### Relationship to `schema_version`

`tool_version` and `schema_version` evolve independently and on different clocks:

- `tool_version` tracks the package release cadence and moves every release.
- `schema_version` tracks record *shape*, is maintained per record type
  (structural health and effectiveness version separately), and changes only
  when a record's shape changes. See the compatibility and bump policy in
  [schemas.md](schemas.md#schema-versioning-and-compatibility).

A package release never bumps `schema_version`, and a schema bump never requires
a particular package version. Deduplication keys on `schema_version` (record
shape), never on `tool_version` (the emitter), so a package release never
fractures a dedupe series and a schema bump intentionally starts a new one.

## Cutting a release

1. **Choose the version** per the policy above (e.g. `0.2.0`).
2. **Update `pyproject.toml`**: set `version = "0.2.0"`.
3. **Update `CHANGELOG.md`**: rename the `[Unreleased]` section to `[0.2.0] - YYYY-MM-DD`,
   add a fresh empty `[Unreleased]`, and update the compare links at the bottom.
4. **Open a PR** with these changes and merge it to `main` after CI passes.
5. **Tag `main`** at the merge commit with a `v`-prefixed tag and push it:
   ```bash
   git checkout main && git pull
   git tag v0.2.0
   git push origin v0.2.0
   ```
6. **Publish a GitHub Release** for that tag (title `v0.2.0`, notes from the
   changelog). Publishing — not tagging — is what triggers the workflow.

Prereleases and drafts are skipped by the workflow, so a draft release can be
prepared without publishing artifacts.

## What the publish workflow does

`.github/workflows/publish.yml` runs on `release: published` (and can be run
manually via `workflow_dispatch` with a `tag_name`):

1. Builds the sdist and wheel with `python -m build`.
2. Uploads them to the release with `gh release upload <tag> dist/* --clobber`.
3. Runs `.github/scripts/gen_index.py`, which fetches every published release,
   collects the package assets, computes/accumulates their SHA-256 hashes in
   `hashes.json`, and writes a PEP 503 index into `pages/`.
4. Deploys `pages/` to the `gh-pages` branch.

The index lists artifacts from **all** published releases, so older versions
remain installable.

## One-time repository setup

- Enable GitHub Pages for the repository, serving from the `gh-pages` branch
  (root). The first successful `publish` run creates that branch.
- No secrets are required beyond the automatic `GITHUB_TOKEN`; the workflow
  requests `contents: write` to upload assets and push `gh-pages`.
