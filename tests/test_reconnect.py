"""Tests for disconnect cleanup, stream buffering, and reconnect."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sony_cisip2 import SonyCISIP2
from sony_cisip2.constants import RECONNECT_INITIAL_DELAY, RECONNECT_MAX_DELAY


def _setup_connected_stream(client: SonyCISIP2) -> AsyncMock:
    """Attach mock reader/writer and mark connected (no live manager)."""
    mock_reader = AsyncMock()
    mock_writer = MagicMock()
    mock_writer.close = MagicMock()
    mock_writer.wait_closed = AsyncMock()
    client._reader = mock_reader
    client._writer = mock_writer
    client._connected = True
    return mock_reader


@pytest.mark.asyncio
async def test_mark_disconnected_fails_pending_commands() -> None:
    """Pending futures fail with ConnectionError on mark-disconnected."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)
    client._connected = True

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    client._pending_responses[42] = future

    await client._mark_disconnected()

    assert not client._connected
    assert future.done()
    with pytest.raises(ConnectionError, match="Disconnected"):
        future.result()


@pytest.mark.asyncio
async def test_notification_loop_exits_on_eof() -> None:
    """Empty read is EOF: loop exits and clears connected."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)
    mock_reader = _setup_connected_stream(client)
    mock_reader.read = AsyncMock(return_value=b"")

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    client._pending_responses[7] = future

    await client._notification_loop()

    assert not client._connected
    with pytest.raises(ConnectionError, match="Disconnected"):
        future.result()


@pytest.mark.asyncio
async def test_notification_loop_exits_on_os_error() -> None:
    """OSError in the read loop marks disconnected and fails pendings."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)
    mock_reader = _setup_connected_stream(client)
    mock_reader.read = AsyncMock(side_effect=OSError("Connection reset"))

    loop = asyncio.get_running_loop()
    future = loop.create_future()
    client._pending_responses[8] = future

    await client._notification_loop()

    assert not client._connected
    with pytest.raises(ConnectionError, match="Disconnected"):
        future.result()


@pytest.mark.asyncio
async def test_fragmented_json_across_reads() -> None:
    """Split JSON object across two reads is reconstituted."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)
    mock_reader = _setup_connected_stream(client)

    part1 = b'{"id":1,"type":"result","value":"o'
    part2 = b'n"}'
    reads = iter([part1, part2, b""])
    mock_reader.read = AsyncMock(side_effect=lambda *_a, **_k: next(reads))

    processed: list[dict] = []

    async def _capture(message: dict) -> None:
        processed.append(message)

    with patch.object(client, "_process_incoming_message", side_effect=_capture):
        await client._notification_loop()

    assert processed == [{"id": 1, "type": "result", "value": "on"}]
    assert not client._connected


@pytest.mark.asyncio
async def test_burst_chunked_json_loses_no_messages() -> None:
    """Many messages chunked across small reads are all processed."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)
    mock_reader = _setup_connected_stream(client)

    messages = [{"id": i, "type": "result", "value": "ACK"} for i in range(1, 21)]
    blob = "".join(json.dumps(m) for m in messages).encode()
    chunk_size = 80
    chunks = [blob[i : i + chunk_size] for i in range(0, len(blob), chunk_size)]
    chunks.append(b"")
    reads = iter(chunks)
    mock_reader.read = AsyncMock(side_effect=lambda *_a, **_k: next(reads))

    processed: list[dict] = []

    async def _capture(message: dict) -> None:
        processed.append(message)

    with patch.object(client, "_process_incoming_message", side_effect=_capture):
        await client._notification_loop()

    assert processed == messages


@pytest.mark.asyncio
async def test_disconnect_cancels_manager_no_reconnect(
    mock_connection: tuple[AsyncMock, MagicMock],
) -> None:
    """Explicit disconnect cancels the manager; no reconnect open attempts."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (mock_reader, mock_writer)
        await client.connect()
        assert client._listener_task is not None
        connect_calls = mock_open.call_count

        await client.disconnect()

        assert client._listener_task is None
        assert not client._connected
        await asyncio.sleep(0.05)
        assert mock_open.call_count == connect_calls


@pytest.mark.asyncio
async def test_connection_manager_exponential_backoff(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reconnect sleeps use 5, 10, 20, … capped at max."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    sleep_delays: list[float] = []
    max_failures = 5
    open_attempts = 0
    loop_count = 0

    async def _one_shot_loop() -> None:
        nonlocal loop_count
        loop_count += 1
        if loop_count > 1:
            raise asyncio.CancelledError
        client._connected = False

    async def _fake_sleep(delay: float) -> None:
        sleep_delays.append(delay)

    async def _fail_then_succeed() -> None:
        nonlocal open_attempts
        open_attempts += 1
        if open_attempts <= max_failures:
            raise ConnectionError("refused")
        client._connected = True

    monkeypatch.setattr(client, "_notification_loop", _one_shot_loop)
    monkeypatch.setattr(asyncio, "sleep", _fake_sleep)
    monkeypatch.setattr(client, "_open_socket", _fail_then_succeed)

    with pytest.raises(asyncio.CancelledError):
        await client._connection_manager()

    assert sleep_delays[0] == RECONNECT_INITIAL_DELAY
    for i in range(1, max_failures):
        expected = min(RECONNECT_INITIAL_DELAY * (2**i), RECONNECT_MAX_DELAY)
        assert sleep_delays[i] == expected


@pytest.mark.asyncio
async def test_reconnect_schedules_on_reconnect_hook(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """on_reconnect is scheduled after reconnect, not awaited inline."""
    hook_started = asyncio.Event()
    hook_finished = asyncio.Event()
    second_loop_entered = asyncio.Event()

    async def _slow_hook() -> None:
        hook_started.set()
        await hook_finished.wait()

    client = SonyCISIP2(host="192.168.1.100", timeout=1.0, on_reconnect=_slow_hook)

    loop_count = 0

    async def _two_loops() -> None:
        nonlocal loop_count
        loop_count += 1
        if loop_count == 1:
            client._connected = False
            return
        second_loop_entered.set()
        await asyncio.Future()

    async def _succeed_open() -> None:
        client._connected = True

    monkeypatch.setattr(client, "_notification_loop", _two_loops)
    monkeypatch.setattr(asyncio, "sleep", AsyncMock())
    monkeypatch.setattr(client, "_open_socket", _succeed_open)

    manager_task = asyncio.create_task(client._connection_manager())

    await asyncio.wait_for(hook_started.wait(), timeout=1.0)
    assert not hook_finished.is_set()
    await asyncio.wait_for(second_loop_entered.wait(), timeout=1.0)

    hook_finished.set()
    manager_task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await manager_task
