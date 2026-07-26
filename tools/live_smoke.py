#!/usr/bin/env python3
"""Live smoke: connect → get power → notify wait → optional volume read-back.

Env:
  CISIP2_HOST       device IP (required)
  CISIP2_PORT       TCP port (default 33336)
  CISIP2_SKIP_EXEC  set to 1 to skip volume write (connect + get only)

Exit 0 on success, 1 on failure, 2 if required env is missing.

Not run in CI. Does not import homeassistant.
"""

from __future__ import annotations

import asyncio
import os
import sys

from sony_cisip2 import SonyCISIP2
from sony_cisip2.constants import DEFAULT_PORT


async def _run(host: str, port: int, *, skip_exec: bool) -> int:
    notifies: list[tuple[str | None, object]] = []

    def on_notify(feature: str | None, value: object) -> None:
        notifies.append((feature, value))
        print(f"notify {feature}={value!r}")

    client = SonyCISIP2(host=host, port=port)
    print(f"connecting {host}:{port} …")
    await client.connect()
    try:
        client.register_notification_callback(None, on_notify)

        power = await client.get_feature("main.power")
        print(f"main.power={power!r}")
        if power is None:
            print("FAIL: get main.power returned None", file=sys.stderr)
            return 1

        # Brief window for any notify traffic (none expected without UI changes).
        await asyncio.sleep(1.0)
        print(f"notifies_seen={len(notifies)}")

        if skip_exec:
            print("done (connect + get; exec skipped)")
            return 0

        if power != "on":
            print("power is not on; skipping volume exec")
            print("done (connect + get; volume exec skipped)")
            return 0

        before = await client.get_feature("main.volumestep")
        print(f"main.volumestep before={before!r}")
        if before is None:
            print("FAIL: get main.volumestep returned None", file=sys.stderr)
            return 1

        try:
            before_int = int(before)
        except (TypeError, ValueError):
            print(f"FAIL: volumestep not an int: {before!r}", file=sys.stderr)
            return 1

        target = before_int + 1 if before_int < 50 else before_int - 1
        result = await client.set_feature("main.volumestep", target)
        print(f"set main.volumestep={target} → {result!r}")
        if result != "ACK":
            print(f"FAIL: expected ACK, got {result!r}", file=sys.stderr)
            return 1

        await asyncio.sleep(0.5)
        after = await client.get_feature("main.volumestep")
        print(f"main.volumestep after={after!r}")
        if after is None or int(after) != target:
            print(
                f"FAIL: expected volumestep={target}, got {after!r}",
                file=sys.stderr,
            )
            return 1

        restore = await client.set_feature("main.volumestep", before_int)
        print(f"restore main.volumestep={before_int} → {restore!r}")

        print("done (volume change confirmed)")
        return 0
    finally:
        await client.disconnect()


def main() -> int:
    host = os.environ.get("CISIP2_HOST")
    if not host:
        print("Set CISIP2_HOST", file=sys.stderr)
        return 2

    port = int(os.environ.get("CISIP2_PORT", str(DEFAULT_PORT)))
    skip_exec = os.environ.get("CISIP2_SKIP_EXEC") == "1"
    return asyncio.run(_run(host, port, skip_exec=skip_exec))


if __name__ == "__main__":
    raise SystemExit(main())
