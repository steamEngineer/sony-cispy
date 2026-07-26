# AGENTS.md

## Behaviour

- Do not post GitHub PR or issue comments without explicit user consent.

## Branching and PRs

- All PRs target `main`.
- Fill in [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md); tick exactly one change type (CI applies the matching label automatically).
- PR title: functional description of the change. Do not use conventional commit prefixes such as `feat:`, `fix:`, or `chore:` — labels categorize PRs, not the title.
- PR body: include a test plan; device-facing protocol changes should note live smoke when applicable.

## Development

- `pip install -e ".[dev]"` — editable install + tools
- `ruff check . && ruff format --check .` — lint/format
- `mypy` — type check
- `pytest -q` — unit tests
- `python -m build && twine check dist/*` — packaging check when metadata/build changes
- Optional live smoke (not CI): `CISIP2_HOST=<ip> python tools/live_smoke.py`
  (`CISIP2_SKIP_EXEC=1` for connect + get only)

Run ruff, mypy, and pytest after code changes.

## Code standards

- Match existing package layout under `src/sony_cisip2/`.
- Runtime dependencies stay empty (stdlib only) unless a PR explicitly adds one.
- `reference/` is historical and must not be included in wheels.
