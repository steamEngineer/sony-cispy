# Tests

This directory contains unit tests for the `sony-cisip2` library.

## Running Tests

### Run all tests

```bash
pytest
```

### Run with verbose output

```bash
pytest -v
```

### Run specific test file

```bash
pytest tests/test_client.py
```

### Run specific test

```bash
pytest tests/test_client.py::test_connect_success
```

### Run with coverage

```bash
pytest --cov=sony_cisip2 --cov-report=html
```

## Test Structure

- `conftest.py` - Pytest fixtures and configuration
- `test_client.py` - Tests for the main `SonyCISIP2` client class
- `test_constants.py` - Tests for constants module
- `test_commandset.py` - Tests for command dictionary
- `test_variables.py` - Tests for variables dictionary

## Test Features

All network connections are mocked, so tests can run without requiring a real Sony device. The tests cover:

- Connection handling (success, failure, timeout)
- Command sending and receiving (get_feature, set_feature)
- Notification callbacks
- JSON stream decoding
- Error handling
- Context manager usage
- Command ID generation and wrapping

## Requirements

Tests require the development dependencies:

```bash
pip install -e ".[dev]"
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines without requiring hardware access.

