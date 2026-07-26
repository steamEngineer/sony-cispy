# sony-cisip2

A modern Python library for controlling Sony Audio/Video Receivers (AVRs) and Soundbars that support the CIS-IP2 protocol over Ethernet/IP.

## Features

- **Robust Connection Handling**: Command ID tracking with futures; auto-reconnect with backoff
- **Universal API**: Generic `get_feature()` / `set_feature()` (return `None` on timeout/miss)
- **Real-time Notifications**: Register callbacks to receive real-time updates when device state changes
- **JSON Stream Decoding**: Multi-message reads with unparsed remainder across TCP fragments
- **Timeout Handling**: Configurable timeouts for all network operations
- **Command Discovery**: Access to the full CIS-IP2 command set via `commands_dict`
- **Async/Await**: Built with modern Python async/await patterns

## Installation

```bash
pip install sony-cisip2
# or from a checkout:
pip install -e ".[dev]"
```

## Basic Usage

```python
import asyncio
from sony_cisip2 import SonyCISIP2

async def main():
    # Create client
    client = SonyCISIP2(host="192.168.1.100", port=33336)
    
    # Connect
    await client.connect()
    
    try:
        # Get power state (None on timeout / miss / NAK / ERR)
        power = await client.get_feature("main.power")
        print(f"Power: {power}")
        
        # Set volume (ACK / NAK / ERR, or None on timeout)
        result = await client.set_feature("main.volumestep", 50)
        print(f"Volume set: {result}")
        
        # Get volume
        volume = await client.get_feature("main.volumestep")
        print(f"Current volume: {volume}")
        
    finally:
        # Disconnect
        await client.disconnect()

asyncio.run(main())
```

## Using Context Manager

```python
import asyncio
from sony_cisip2 import SonyCISIP2

async def main():
    async with SonyCISIP2(host="192.168.1.100") as client:
        power = await client.get_feature("main.power")
        print(f"Power: {power}")
        
        await client.set_feature("main.power", "on")

asyncio.run(main())
```

## Notification Callbacks

Register callbacks to receive real-time notifications when device state changes:

```python
import asyncio
from sony_cisip2 import SonyCISIP2

async def on_power_change(feature, value):
    print(f"Power changed to: {value}")

async def on_volume_change(feature, value):
    print(f"Volume changed to: {value}")

async def on_any_change(feature, value):
    print(f"{feature} changed to {value}")

async def main():
    client = SonyCISIP2(host="192.168.1.100")
    await client.connect()
    
    try:
        # Register callbacks
        client.register_notification_callback("main.power", on_power_change)
        client.register_notification_callback("main.volumestep", on_volume_change)
        client.register_notification_callback(None, on_any_change)  # All notifications
        
        # Keep running to receive notifications
        await asyncio.sleep(60)
        
    finally:
        await client.disconnect()

asyncio.run(main())
```

## Command Discovery

Access the full CIS-IP2 command set to discover available features:

```python
from sony_cisip2 import commands_dict

# List all available commands
for feature, details in commands_dict.items():
    print(f"{feature}: {details['description']}")
    print(f"  Set: {details['set']}, Get: {details['get']}, Notify: {details['notify']}")
```

## Common Features

### Power Control
- `main.power` - Get/set power state ("on", "off", "toggle")

### Volume Control
- `main.volumestep` - Volume in steps (0-100)
- `main.volumedb` - Volume in dB (-92.0 to 23.0)
- `main.mute` - Mute state ("on", "off", "toggle")

### Input Selection
- `main.input` - Current input source (varies by device)

### Audio Settings
- `audio.soundfield` - Sound field mode
- `audio.voiceenhancer` - Voice enhancer ("upon", "upoff")

### System Settings
- `system.volumedisplay` - Volume display mode ("db", "step")

## Requirements

- Python 3.12+
- asyncio (standard library)

## License

This library is provided as-is. Use at your own risk.

## Disclaimer

This library is not officially supported by Sony. Use at your own risk.
