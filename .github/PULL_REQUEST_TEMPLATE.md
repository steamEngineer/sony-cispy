# What does this implement/fix?

<!-- Quick description and explanation of changes. -->

**Related issue (if applicable):**

- related issue <link to issue>

## Types of changes

<!--
Tick exactly one box. CI (.github/workflows/pr-labels.yaml) applies the
GitHub label shown in backticks; release drafter uses that label in the
changelog. Label names match .github/labels.yml descriptions.
-->

- [ ] Bugfix — `bugfix`
- [ ] New feature — `new-feature`
- [ ] Enhancement to an existing feature — `enhancement`
- [ ] Breaking change — `breaking-change`
- [ ] Refactor (no behaviour change) — `refactor`
- [ ] Documentation only — `documentation`
- [ ] Maintenance / chore — `maintenance`
- [ ] CI / workflow change — `ci`
- [ ] Dependencies bump — `dependencies`
- [ ] Skip changelog — `skip-changelog`

## Checklist

- [ ] The code change is tested and works locally.
- [ ] `pytest -q` passes, and tests have been added/updated under `tests/` where applicable.
- [ ] `ruff check . && ruff format --check .` and `mypy` pass.
- [ ] `python -m build && twine check dist/*` when packaging/metadata changed.

## Test plan

<!-- How was this tested? Include manual steps for device-facing changes. -->
