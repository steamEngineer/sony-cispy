"""Example usage of the sony-cisip2 library."""

import asyncio

from sony_cisip2 import SonyCISIP2


async def example_basic_usage():
    """Basic example of connecting and sending commands."""
    # Create client (replace with your device IP)
    client = SonyCISIP2(host="10.0.110.130", port=33336)

    try:
        # Connect to device
        print("Connecting...")
        await client.connect()
        print("Connected!")

        # Get power state
        power = await client.get_feature("main.power")
        print(f"Current power state: {power}")

        # Set volume
        result = await client.set_feature("main.volumestep", 10)
        print(f"Set volume result: {result}")

        # Get volume
        volume = await client.get_feature("main.volumestep")
        print(f"Current volume: {volume}")

        # Get input
        input_source = await client.get_feature("main.input")
        print(f"Current input: {input_source}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await client.disconnect()
        print("Disconnected")


async def example_context_manager():
    """Example using context manager."""
    async with SonyCISIP2(host="10.0.110.130") as client:
        power = await client.get_feature("main.power")
        print(f"Power: {power}")


async def example_notifications():
    """Example with notification callbacks."""

    async def on_power_change(feature, value):
        print(f"⚡ Power changed to: {value}")

    async def on_volume_change(feature, value):
        print(f"🔊 Volume changed to: {value}")

    async def on_any_change(feature, value):
        print(f"📢 {feature} changed to {value}")

    client = SonyCISIP2(host="10.0.110.130")

    try:
        await client.connect()

        # Register callbacks
        client.register_notification_callback("main.power", on_power_change)
        client.register_notification_callback("main.volumestep", on_volume_change)
        client.register_notification_callback(None, on_any_change)  # All notifications

        print("Listening for notifications for 30 seconds...")
        print("(Try changing volume or power on the device)")
        await asyncio.sleep(30)

    finally:
        await client.disconnect()


async def example_command_discovery():
    """Example of discovering available commands."""
    from sony_cisip2 import commands_dict

    print("Available CIS-IP2 commands:")
    print("=" * 60)

    # Show first 10 commands as example
    for i, (feature, details) in enumerate(commands_dict.items()):
        if i >= 10:
            print(f"\n... and {len(commands_dict) - 10} more commands")
            break

        print(f"\n{feature}")
        print(f"  Description: {details['description']}")
        print(
            f"  Set: {details['set']}, Get: {details['get']}, "
            f"Notify: {details['notify']}"
        )


if __name__ == "__main__":
    print("Sony CIS-IP2 Library Examples")
    print("=" * 60)
    print("\nNote: Replace '10.0.110.130' with your device IP address")
    print("\nUncomment the example you want to run:\n")

    # Uncomment the example you want to run:
    asyncio.run(example_basic_usage())
    # asyncio.run(example_context_manager())
    # asyncio.run(example_notifications())
    asyncio.run(example_command_discovery())
