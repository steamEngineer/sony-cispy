"""Pytest configuration and fixtures."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest

from sony_cisip2 import SonyCISIP2


@pytest.fixture
def mock_reader() -> AsyncMock:
    """Create a mock StreamReader."""
    reader = AsyncMock()
    reader.read = AsyncMock(return_value=b"")
    return reader


@pytest.fixture
def mock_writer() -> MagicMock:
    """Create a mock StreamWriter."""
    writer = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    return writer


@pytest.fixture
def mock_connection(
    mock_reader: AsyncMock, mock_writer: MagicMock
) -> tuple[AsyncMock, MagicMock]:
    """Create a mock connection (reader, writer)."""
    return mock_reader, mock_writer


@pytest.fixture
def client() -> SonyCISIP2:
    """Create a SonyCISIP2 client instance."""
    return SonyCISIP2(host="192.168.1.100", port=33336, timeout=1.0)


@pytest.fixture
def event_loop() -> AsyncGenerator[asyncio.AbstractEventLoop, None]:
    """Create an event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_get_response() -> dict:
    """Sample GET response from device."""
    return {
        "id": 10,
        "type": "result",
        "feature": "main.power",
        "value": "on",
    }


@pytest.fixture
def sample_set_response() -> dict:
    """Sample SET response from device."""
    return {
        "id": 11,
        "type": "result",
        "value": "ACK",
    }


@pytest.fixture
def sample_notification() -> dict:
    """Sample notification from device."""
    return {
        "type": "notify",
        "feature": "main.power",
        "value": "off",
    }
