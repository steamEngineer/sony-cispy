# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Hatchling packaging as PyPI name `sony-cisip2` (import `sony_cisip2`).
- `src/` layout, `__version__ = "0.1.0a0"`, CI (lint/mypy/pytest matrix/build),
  and tag-based Publish workflow with Trusted Publishing.
- Changelog, releasing docs, and agent/PR templates mirrored from sibling
  packaging practices.

### Changed

- Renamed import package from `sony_cispy` to `sony_cisip2`.
- Requires Python 3.12+ (was marketed as 3.13+).
