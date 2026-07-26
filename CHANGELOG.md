# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0a1] - 2026-07-26

### Added

- Hatchling packaging as PyPI name `sony-cisip2` (import `sony_cisip2`).
- `src/` layout, initial `__version__` / Hatch packaging, CI
  (lint/mypy/pytest matrix/build), and tag-based Publish workflow with
  Trusted Publishing.
- Changelog, releasing docs, and agent/PR templates mirrored from sibling
  packaging practices.
- Auto-reconnect with exponential backoff after unexpected TCP drops
  (`RECONNECT_INITIAL_DELAY` / `RECONNECT_MAX_DELAY`); optional `on_reconnect`
  hook scheduled after a successful reconnect.
- `tools/live_smoke.py` for manual device smoke (`CISIP2_HOST`; not run in CI).

### Changed

- Renamed import package from `sony_cispy` to `sony_cisip2`.
- Requires Python 3.12+ (was marketed as 3.13+).
- `get_feature` returns `None` on timeout, miss, NAK, or ERR (no
  `"Unknown Value"` sentinel).
- `set_feature` returns the device result string (`ACK` / `NAK` / `ERR`) or
  `None` on timeout/miss (no `"Unknown Response"` sentinel).
- `is_connected` reflects the connection flag only (no probe get).
- JSON stream decode keeps an unparsed remainder across TCP reads.
- Commands require an established connection (no lazy connect from send).

### Fixed

- Empty TCP read (EOF) and listener `OSError` mark the client disconnected and
  fail pending command futures.

[Unreleased]: https://github.com/steamEngineer/sony-cispy/compare/v0.1.0a1...HEAD
[0.1.0a1]: https://github.com/steamEngineer/sony-cispy/releases/tag/v0.1.0a1
