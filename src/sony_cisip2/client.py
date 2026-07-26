"""Client for communicating with Sony CIS-IP2 compatible devices."""

from __future__ import annotations

import asyncio
from collections.abc import Callable
import contextlib
import json
import logging
from typing import TYPE_CHECKING, Any

from .constants import (
    CMD_ID_INITIAL,
    CMD_ID_MAX,
    DEFAULT_PORT,
    MSG_TYPE_GET,
    MSG_TYPE_NOTIFY,
    MSG_TYPE_RESULT,
    MSG_TYPE_SET,
    TCP_TIMEOUT,
)

if TYPE_CHECKING:
    from collections.abc import Awaitable

_LOGGER = logging.getLogger(__name__)


class SonyCISIP2:
    """Client for Sony CIS-IP2 protocol communication.

    This class provides a robust, modern implementation for controlling Sony
    Audio/Video Receivers (AVRs) and Soundbars that support the CIS-IP2 protocol.

    Features:
    - Command ID tracking with futures for reliable request/response matching
    - JSON stream decoding for handling multiple messages in one read
    - Timeout handling for all network operations
    - Real-time notification callbacks
    - Generic get_feature/set_feature API
    - Automatic connection management
    """

    def __init__(
        self,
        host: str,
        port: int = DEFAULT_PORT,
        timeout: float = TCP_TIMEOUT,
    ) -> None:
        """Initialize the Sony CIS-IP2 client.

        Args:
            host: IP address of the Sony device
            port: TCP port (default: 33336)
            timeout: Timeout for network operations in seconds (default: 10.0)
        """
        self.host = host
        self.port = port
        self.timeout = timeout

        # Connection state
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._connected = False
        self._listening = False

        # Command tracking
        self._command_id_counter = CMD_ID_INITIAL
        self._command_lock = asyncio.Lock()
        self._pending_responses: dict[int, asyncio.Future[dict[str, Any]]] = {}

        # Notification callbacks
        self._notification_callbacks: dict[str | None, list[Callable]] = {}

        # Background listener task
        self._listener_task: asyncio.Task | None = None

        # Logger
        self.logger = _LOGGER

    async def connect(self) -> None:
        """Connect to the Sony device.

        Raises:
            ConnectionError: If connection fails
        """
        if self._connected:
            return

        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port),
                timeout=self.timeout,
            )
            # Give the connection a moment to stabilize
            await asyncio.sleep(0.1)
            self._connected = True
            self.logger.info("Connected to Sony device at %s:%s", self.host, self.port)

            # Start listening for notifications
            await self._start_notification_listener()

        except TimeoutError as err:
            # TimeoutError subclasses OSError on 3.10+; handle before OSError.
            self._connected = False
            self.logger.exception("Connection timeout")
            raise ConnectionError(f"Connection timeout: {err}") from err
        except OSError as err:
            self._connected = False
            self.logger.exception("Failed to connect to Sony device")
            raise ConnectionError(f"Failed to connect: {err}") from err

    async def disconnect(self) -> None:
        """Disconnect from the Sony device."""
        self._listening = False

        # Cancel listener task
        if self._listener_task:
            self._listener_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._listener_task
            self._listener_task = None

        # Close connection
        if self._writer:
            self._writer.close()
            with contextlib.suppress(OSError):
                await self._writer.wait_closed()

        self._reader = None
        self._writer = None
        self._connected = False

        # Fail any pending command futures
        for future in self._pending_responses.values():
            if not future.done():
                future.set_exception(ConnectionError("Disconnected"))
        self._pending_responses.clear()

        self.logger.info("Disconnected from Sony device")

    async def is_connected(self) -> bool:
        """Check if connected to the device.

        Returns:
            True if connected, False otherwise
        """
        if not self._connected:
            return False

        # Try a simple command to verify connection
        try:
            await self.get_feature("main.power")
            return True
        except Exception:
            return False

    async def get_feature(self, feature: str) -> Any:
        """Get the value of a feature.

        This is a universal method that works with any CIS-IP2 feature.

        Args:
            feature: The feature name (e.g., "main.power", "main.volumestep")

        Returns:
            The feature value, or "Unknown Value" if the request fails

        Example:
            >>> power = await client.get_feature("main.power")
            >>> volume = await client.get_feature("main.volumestep")
        """
        response = await self._send_command(MSG_TYPE_GET, feature)
        if response and response.get("type") == MSG_TYPE_RESULT:
            return response.get("value", "Unknown Value")
        return "Unknown Value"

    async def set_feature(self, feature: str, value: Any) -> str:
        """Set a feature to a specific value.

        This is a universal method that works with any CIS-IP2 feature.

        Args:
            feature: The feature name (e.g., "main.power", "main.volumestep")
            value: The value to set (can be string, number, etc.)

        Returns:
            "ACK" if successful, "NAK", "ERR", or "Unknown Response" otherwise

        Example:
            >>> result = await client.set_feature("main.power", "on")
            >>> result = await client.set_feature("main.volumestep", 50)
        """
        response = await self._send_command(MSG_TYPE_SET, feature, value)
        if response and response.get("type") == MSG_TYPE_RESULT:
            return response.get("value", "Unknown Response")
        return "Unknown Response"

    def register_notification_callback(
        self,
        feature: str | None,
        callback: Callable[[str, Any], Awaitable[None] | None],
    ) -> None:
        """Register a callback function for notifications.

        Args:
            feature: The feature name to listen for, or None for all features
            callback: The callback function that will be called with (feature, value)

        Example:
            >>> async def on_power_change(feature, value):
            ...     print(f"Power changed to {value}")
            >>> client.register_notification_callback("main.power", on_power_change)

            >>> async def on_any_change(feature, value):
            ...     print(f"{feature} changed to {value}")
            >>> client.register_notification_callback(None, on_any_change)
        """
        if feature not in self._notification_callbacks:
            self._notification_callbacks[feature] = []
        if callback not in self._notification_callbacks[feature]:
            self._notification_callbacks[feature].append(callback)

    def unregister_notification_callback(
        self,
        feature: str | None,
        callback: Callable[[str, Any], Awaitable[None] | None],
    ) -> None:
        """Unregister a notification callback.

        Args:
            feature: The feature name, or None for all features
            callback: The callback function to remove
        """
        if (
            feature in self._notification_callbacks
            and callback in self._notification_callbacks[feature]
        ):
            self._notification_callbacks[feature].remove(callback)
            if not self._notification_callbacks[feature]:
                del self._notification_callbacks[feature]

    async def _start_notification_listener(self) -> None:
        """Start the notification listener task."""
        if self._listener_task and not self._listener_task.done():
            return

        if not self._connected:
            await self.connect()

        self._listener_task = asyncio.create_task(self._notification_loop())

    async def _notification_loop(self) -> None:
        """Listen for real-time notifications from the device."""
        self._listening = True
        self.logger.info("Starting notification listener")

        try:
            while self._listening and self._connected:
                try:
                    if not self._reader:
                        break

                    data = await asyncio.wait_for(self._reader.read(1024), timeout=1.0)

                    if not data:
                        await asyncio.sleep(0.1)
                        continue

                    response_str = data.decode("utf-8", errors="replace").strip()
                    if not response_str:
                        continue

                    messages = self._decode_json_stream(response_str)
                    if not messages:
                        continue

                    for message in messages:
                        await self._process_incoming_message(message)

                except TimeoutError:
                    continue
                except asyncio.CancelledError:
                    raise
                except OSError:
                    self.logger.exception("Error in notification listener")
                    await asyncio.sleep(1.0)
        except asyncio.CancelledError:
            self.logger.info("Notification listener cancelled")
            raise
        finally:
            self._listening = False
            self.logger.info("Notification listener stopped")

    async def _send_command(
        self,
        message_type: str,
        feature: str,
        value: Any = None,
    ) -> dict[str, Any] | None:
        """Send a command and wait for response.

        Args:
            message_type: "get" or "set"
            feature: The feature name
            value: Optional value for "set" commands

        Returns:
            The response message, or None on timeout/error
        """
        if not self._connected:
            await self.connect()

        if not self._writer or not self._reader:
            raise ConnectionError("Not connected to device")

        if not self._listener_task or self._listener_task.done():
            await self._start_notification_listener()

        response_future: asyncio.Future[dict[str, Any]] | None = None
        command_id: int | None = None

        async with self._command_lock:
            try:
                # Assign a unique command id
                command: dict[str, Any] = {
                    "type": message_type,
                    "feature": feature,
                }
                if value is not None:
                    command["value"] = value

                command_id = self._get_next_command_id()
                command["id"] = command_id

                loop = asyncio.get_running_loop()
                response_future = loop.create_future()
                self._pending_responses[command_id] = response_future

                command_json = json.dumps(command) + "\n"
                self.logger.debug("Sending command: %s", command_json.strip())
                self._writer.write(command_json.encode())
                await self._writer.drain()
            except OSError as err:
                if command_id is not None and command_id in self._pending_responses:
                    self._pending_responses.pop(command_id, None)
                self.logger.exception("Error sending command")
                raise ConnectionError(f"Error sending command: {err}") from err

        try:
            response = await asyncio.wait_for(response_future, timeout=self.timeout)
            return response
        except TimeoutError:
            if response_future and not response_future.done():
                response_future.cancel()
            self.logger.warning("Timeout waiting for response to command: %s", command)
            return None
        finally:
            if command_id is not None:
                self._pending_responses.pop(command_id, None)

    def _get_next_command_id(self) -> int:
        """Return a unique command id."""
        self._command_id_counter += 1
        if self._command_id_counter > CMD_ID_MAX:
            self._command_id_counter = CMD_ID_INITIAL
        return self._command_id_counter

    def _decode_json_stream(self, data: str) -> list[dict[str, Any]]:
        """Decode one or more JSON objects from a buffer string.

        Handles cases where multiple JSON objects arrive in a single read.
        """
        messages: list[dict[str, Any]] = []
        if not data:
            return messages

        decoder = json.JSONDecoder()
        idx = 0
        length = len(data)

        while idx < length:
            # Skip whitespace between JSON objects
            while idx < length and data[idx].isspace():
                idx += 1

            if idx >= length:
                break

            try:
                message, end = decoder.raw_decode(data, idx)
                messages.append(message)
                idx = end
            except json.JSONDecodeError as err:
                self.logger.warning(
                    "Failed to decode JSON chunk: %s (remaining=%s)",
                    err,
                    data[idx:],
                )
                break

        return messages

    async def _process_incoming_message(self, message: dict[str, Any]) -> None:
        """Process a single incoming message from the device."""
        if not message:
            return

        msg_type = message.get("type")
        feature = message.get("feature")
        value = message.get("value")

        self.logger.debug(
            "Processing message type=%s feature=%s value=%s",
            msg_type,
            feature,
            value,
        )

        if msg_type == MSG_TYPE_RESULT:
            self._resolve_pending_response(message)

        if msg_type == MSG_TYPE_NOTIFY:
            await self._dispatch_notification_callbacks(feature, value)

    def _resolve_pending_response(self, message: dict[str, Any]) -> None:
        """Resolve the future waiting for a command response."""
        command_id = message.get("id")
        if command_id is None:
            return

        future = self._pending_responses.get(command_id)
        if future and not future.done():
            future.set_result(message)

    async def _dispatch_notification_callbacks(
        self, feature: str | None, value: Any
    ) -> None:
        """Invoke registered callbacks for a notification."""
        # Call feature-specific callbacks
        if feature and feature in self._notification_callbacks:
            for callback in self._notification_callbacks[feature]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(feature, value)
                    else:
                        callback(feature, value)
                except Exception:
                    self.logger.exception("Error in notification callback")

        # Call general callbacks (None key)
        if None in self._notification_callbacks:
            for callback in self._notification_callbacks[None]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(feature, value)
                    else:
                        callback(feature, value)
                except Exception:
                    self.logger.exception("Error in notification callback")

    async def __aenter__(self) -> SonyCISIP2:
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.disconnect()
