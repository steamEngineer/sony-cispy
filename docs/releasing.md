# Releasing

1. Bump `__version__` in `src/sony_cisip2/__init__.py` (single source of truth).
2. Move `[Unreleased]` notes into a new `CHANGELOG.md` section for that version
   (and update compare links at the bottom of the file when present).
3. Commit, push to `main`, then tag and push:
   ```bash
   git tag vX.Y.ZaN
   git push origin vX.Y.ZaN
   ```
4. The Publish workflow builds, checks that the tag matches the wheel version,
   uploads `sony-cisip2` to PyPI via Trusted Publishing, and creates a GitHub
   Release from the matching changelog section.

The first PyPI publish is planned as **`0.1.0a1`** (tag `v0.1.0a1`). In-tree
`0.1.0a0` is a packaging placeholder and is not intended for a tag.

## One-time: PyPI Trusted Publisher

Before the first tag that should upload to PyPI, add a **pending Trusted
Publisher** on PyPI for project **`sony-cisip2`**:

| Field | Value |
|-------|--------|
| Owner | `steamEngineer` |
| Repository | `sony-cispy` |
| Workflow | `publish.yml` |
| Environment | `pypi` |

The first successful tagged Publish run creates the PyPI project.
