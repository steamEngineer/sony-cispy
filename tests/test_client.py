"""Tests for SonyCISIP2 client."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from sony_cisip2 import SonyCISIP2
from sony_cisip2.constants import DEFAULT_PORT, MSG_TYPE_SET


async def _resolve_pending(client: SonyCISIP2, command_id: int, response: dict) -> None:
    """Resolve the pending future `_send_command` creates for `command_id`."""
    for _ in range(100):
        fut = client._pending_responses.get(command_id)
        if fut is not None and not fut.done():
            fut.set_result(response)
            return
        await asyncio.sleep(0.01)
    raise AssertionError(f"pending response {command_id} never appeared")


@pytest.mark.asyncio
async def test_client_initialization():
    """Test client initialization."""
    client = SonyCISIP2(host="192.168.1.100", port=33336, timeout=5.0)

    assert client.host == "192.168.1.100"
    assert client.port == 33336
    assert client.timeout == 5.0
    assert not client._connected
    assert client._reader is None
    assert client._writer is None


@pytest.mark.asyncio
async def test_client_default_values():
    """Test client default values."""
    client = SonyCISIP2(host="192.168.1.100")

    assert client.port == DEFAULT_PORT
    assert client.timeout == 10.0


@pytest.mark.asyncio
async def test_connect_success(mock_connection):
    """Test successful connection."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (mock_reader, mock_writer)

        await client.connect()

        assert client._connected
        assert client._reader == mock_reader
        assert client._writer == mock_writer
        mock_open.assert_called_once_with("192.168.1.100", DEFAULT_PORT)


@pytest.mark.asyncio
async def test_connect_failure():
    """Test connection failure."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.side_effect = OSError("Connection refused")

        with pytest.raises(ConnectionError, match="Failed to connect"):
            await client.connect()

        assert not client._connected


@pytest.mark.asyncio
async def test_connect_timeout():
    """Test connection timeout."""
    client = SonyCISIP2(host="192.168.1.100", timeout=0.1)

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.side_effect = TimeoutError()

        with pytest.raises(ConnectionError, match="Connection timeout"):
            await client.connect()

        assert not client._connected


@pytest.mark.asyncio
async def test_disconnect(mock_connection):
    """Test disconnection."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (mock_reader, mock_writer)

        await client.connect()
        assert client._connected

        await client.disconnect()

        assert not client._connected
        assert client._reader is None
        assert client._writer is None
        mock_writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_disconnect_with_listener_task(mock_connection):
    """Test disconnection cancels listener task."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    # Mock the reader to return data that will timeout
    mock_reader.read = AsyncMock(side_effect=TimeoutError())

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (mock_reader, mock_writer)

        await client.connect()
        await client._start_notification_listener()

        assert client._listener_task is not None

        await client.disconnect()

        assert client._listener_task is None


@pytest.mark.asyncio
async def test_get_feature_success(mock_connection):
    """Test getting a feature value."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    # Mock response data
    response = {"id": 10, "type": "result", "feature": "main.power", "value": "on"}

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (mock_reader, mock_writer)

        await client.connect()

        asyncio.create_task(_resolve_pending(client, 10, response))

        with patch.object(client, "_get_next_command_id", return_value=10):
            result = await client.get_feature("main.power")

        assert result == "on"


@pytest.mark.asyncio
async def test_set_feature_success(mock_connection):
    """Test setting a feature value."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    # Mock response data
    response = {"id": 11, "type": "result", "value": "ACK"}

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (mock_reader, mock_writer)

        await client.connect()

        asyncio.create_task(_resolve_pending(client, 11, response))

        with patch.object(client, "_get_next_command_id", return_value=11):
            result = await client.set_feature("main.power", "on")

        assert result == "ACK"
        # Verify command was written
        assert mock_writer.write.called
        written_data = mock_writer.write.call_args[0][0].decode()
        command = json.loads(written_data.strip())
        assert command["type"] == MSG_TYPE_SET
        assert command["feature"] == "main.power"
        assert command["value"] == "on"


@pytest.mark.asyncio
async def test_set_feature_with_none_value(mock_connection):
    """Test setting a feature with None value."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    response = {"id": 12, "type": "result", "value": "ACK"}

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (mock_reader, mock_writer)

        await client.connect()

        asyncio.create_task(_resolve_pending(client, 12, response))

        with patch.object(client, "_get_next_command_id", return_value=12):
            result = await client.set_feature("main.power", None)

        assert result == "ACK"
        written_data = mock_writer.write.call_args[0][0].decode()
        command = json.loads(written_data.strip())
        assert "value" not in command


@pytest.mark.asyncio
async def test_command_timeout(mock_connection):
    """Test command timeout."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=0.1)

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (mock_reader, mock_writer)

        await client.connect()

        # Create a future that will never complete
        response_future = asyncio.Future()
        client._pending_responses[13] = response_future

        with patch.object(client, "_get_next_command_id", return_value=13):
            result = await client.get_feature("main.power")

        # Should return "Unknown Value" on timeout
        assert result == "Unknown Value"
        # Future should be cancelled/cleaned up
        assert 13 not in client._pending_responses


@pytest.mark.asyncio
async def test_notification_callback(mock_connection):
    """Test notification callback registration and invocation."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    callback_called = False
    callback_feature = None
    callback_value = None

    async def test_callback(feature, value):
        nonlocal callback_called, callback_feature, callback_value
        callback_called = True
        callback_feature = feature
        callback_value = value

    client.register_notification_callback("main.power", test_callback)

    # Simulate notification
    notification = {
        "type": "notify",
        "feature": "main.power",
        "value": "off",
    }

    await client._process_incoming_message(notification)

    assert callback_called
    assert callback_feature == "main.power"
    assert callback_value == "off"


@pytest.mark.asyncio
async def test_notification_callback_all_features(mock_connection):
    """Test notification callback for all features."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    callback_calls = []

    async def test_callback(feature, value):
        callback_calls.append((feature, value))

    client.register_notification_callback(None, test_callback)

    # Simulate multiple notifications
    notifications = [
        {"type": "notify", "feature": "main.power", "value": "on"},
        {"type": "notify", "feature": "main.volumestep", "value": "50"},
    ]

    for notification in notifications:
        await client._process_incoming_message(notification)

    assert len(callback_calls) == 2
    assert callback_calls[0] == ("main.power", "on")
    assert callback_calls[1] == ("main.volumestep", "50")


@pytest.mark.asyncio
async def test_unregister_notification_callback(mock_connection):
    """Test unregistering a notification callback."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    callback_called = False

    async def test_callback(feature, value):
        nonlocal callback_called
        callback_called = True

    client.register_notification_callback("main.power", test_callback)
    client.unregister_notification_callback("main.power", test_callback)

    notification = {
        "type": "notify",
        "feature": "main.power",
        "value": "off",
    }

    await client._process_incoming_message(notification)

    assert not callback_called


@pytest.mark.asyncio
async def test_json_stream_decoding():
    """Test JSON stream decoding with multiple messages."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    # Simulate multiple JSON objects in one string
    json_stream = (
        '{"id":1,"type":"result","value":"ACK"}\n'
        '{"type":"notify","feature":"main.power","value":"on"}\n'
        '{"id":2,"type":"result","value":"50"}'
    )

    messages = client._decode_json_stream(json_stream)

    assert len(messages) == 3
    assert messages[0]["id"] == 1
    assert messages[1]["type"] == "notify"
    assert messages[2]["value"] == "50"


@pytest.mark.asyncio
async def test_json_stream_decoding_whitespace():
    """Test JSON stream decoding with whitespace."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    json_stream = '   {"id":1,"type":"result"}   \n\n   {"id":2,"type":"result"}   '

    messages = client._decode_json_stream(json_stream)

    assert len(messages) == 2
    assert messages[0]["id"] == 1
    assert messages[1]["id"] == 2


@pytest.mark.asyncio
async def test_json_stream_decoding_invalid():
    """Test JSON stream decoding with invalid JSON."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    json_stream = '{"id":1,"type":"result"}{invalid json}'

    messages = client._decode_json_stream(json_stream)

    # Should decode the first valid JSON and stop at invalid
    assert len(messages) == 1
    assert messages[0]["id"] == 1


@pytest.mark.asyncio
async def test_context_manager(mock_connection):
    """Test async context manager."""
    mock_reader, mock_writer = mock_connection

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (mock_reader, mock_writer)

        async with SonyCISIP2(host="192.168.1.100", timeout=1.0) as client:
            assert client._connected

        assert not client._connected


@pytest.mark.asyncio
async def test_command_id_generation():
    """Test command ID generation and wrapping."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    # Set counter near max
    client._command_id_counter = 999999

    id1 = client._get_next_command_id()
    assert id1 == 1000000

    id2 = client._get_next_command_id()
    # Should wrap back to initial value
    assert id2 == 10


@pytest.mark.asyncio
async def test_is_connected_not_connected():
    """Test is_connected when not connected."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    assert not await client.is_connected()


@pytest.mark.asyncio
async def test_is_connected_success(mock_connection):
    """Test is_connected when connected."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    response = {"id": 10, "type": "result", "feature": "main.power", "value": "on"}

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (mock_reader, mock_writer)

        await client.connect()

        asyncio.create_task(_resolve_pending(client, 10, response))

        with patch.object(client, "_get_next_command_id", return_value=10):
            result = await client.is_connected()

        assert result


@pytest.mark.asyncio
async def test_response_matching():
    """Test that responses are matched to correct command IDs."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    # Create multiple pending responses
    future1 = asyncio.Future()
    future2 = asyncio.Future()
    client._pending_responses[100] = future1
    client._pending_responses[200] = future2

    # Resolve response for command 100
    response1 = {"id": 100, "type": "result", "value": "first"}
    client._resolve_pending_response(response1)

    assert future1.done()
    assert future1.result() == response1
    assert not future2.done()

    # Resolve response for command 200
    response2 = {"id": 200, "type": "result", "value": "second"}
    client._resolve_pending_response(response2)

    assert future2.done()
    assert future2.result() == response2


@pytest.mark.asyncio
async def test_response_without_id():
    """Test handling response without ID."""
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    future = asyncio.Future()
    client._pending_responses[100] = future

    # Response without ID should not resolve anything
    response = {"type": "result", "value": "ACK"}
    client._resolve_pending_response(response)

    assert not future.done()


@pytest.mark.asyncio
async def test_connect_when_already_connected(mock_connection):
    """Test connecting when already connected."""
    mock_reader, mock_writer = mock_connection
    client = SonyCISIP2(host="192.168.1.100", timeout=1.0)

    with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
        mock_open.return_value = (mock_reader, mock_writer)

        await client.connect()
        assert client._connected

        # Connect again should not create new connection
        call_count = mock_open.call_count
        await client.connect()
        assert mock_open.call_count == call_count  # No new call
