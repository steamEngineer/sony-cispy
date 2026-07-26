# sony-cisip2

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/steamEngineer/sony-cispy/actions/workflows/ci.yml/badge.svg)](https://github.com/steamEngineer/sony-cispy/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

HA-agnostic async Python client for Sony CIS-IP2 over Ethernet/IP (TCP port
33336). Control power, volume, inputs, and other features on compatible Sony
AVRs and soundbars on your local network.

The **GitHub repository** is named `sony-cispy`. The **PyPI package** and
**import** are `sony-cisip2` / `sony_cisip2`.

**CIS** stands for Custom Installation Services (or Solutions) — the
Sony-specific local control protocol used by custom-install systems.

This is a **protocol library**, not a Home Assistant integration. Integrations
that speak CIS-IP2 can depend on this package.

## Status

**Alpha** (`0.1.0a1` on PyPI). APIs may change before 1.0. See
[CHANGELOG.md](CHANGELOG.md).

## Features

- Universal `get_feature()` / `set_feature()` API for any CIS-IP2 feature
- Command ID tracking with futures for reliable request/response matching
- Real-time notification callbacks
- JSON stream decoding with remainder across TCP read fragments
- Auto-reconnect with exponential backoff after unexpected drops
- Full command catalog via `commands_dict`
- Stdlib only (no runtime dependencies)
- Async/await (Python 3.12+)

## Device compatibility

Enable IP/network control on the device (menu names vary: "External Control",
"Simple IP Control", "IP Control", etc.). Quick check with netcat:

```bash
netcat <IP_ADDRESS> 33336
{"id":3, "type":"get","feature":"main.power"}
```

A JSON result for `main.power` means the port is reachable and control is on.

## Install

Requires Python 3.12+.

```bash
pip install sony-cisip2
```

From a checkout:

```bash
pip install -e ".[dev]"
```

## Quickstart

```python
import asyncio
from sony_cisip2 import SonyCISIP2

async def main():
    async with SonyCISIP2(host="192.168.1.100") as client:
        power = await client.get_feature("main.power")
        if power is None:
            print("get main.power timed out or failed")
            return
        print(f"Power: {power}")
        result = await client.set_feature("main.volumestep", 50)
        print(f"set volume: {result}")

asyncio.run(main())
```

See [example.py](example.py) and [src/sony_cisip2/README.md](src/sony_cisip2/README.md)
for notifications, command discovery, and more features.

## Requirements

- **Python**: 3.12 or higher
- **Dependencies**: none (standard library only)

## Project layout

```
sony-cispy/                 # GitHub repo root
├── src/sony_cisip2/        # Installable package
│   ├── client.py           # SonyCISIP2
│   ├── commandset.py
│   ├── constants.py
│   └── variables.py
├── tests/
├── tools/live_smoke.py     # Manual device smoke (CISIP2_HOST; not in CI)
├── reference/              # Historical sources (not shipped in the wheel)
├── example.py
└── pyproject.toml
```

## Development

```bash
pip install -e ".[dev]"
ruff check . && ruff format --check .
mypy
pytest -q
python -m build && twine check dist/*
```

Optional live smoke against a device on your LAN (not run in CI):

```bash
CISIP2_HOST=<device-ip> CISIP2_SKIP_EXEC=1 python tools/live_smoke.py
CISIP2_HOST=<device-ip> python tools/live_smoke.py
```

Release process: [docs/releasing.md](docs/releasing.md).

## Credits

- [@liudger](https://github.com/liudger) (Willem-Jan van Rootselaar) — substantial CIS-IP2 client work in [bravia-quad-homeassistant](https://github.com/steamEngineer/bravia-quad-homeassistant) (reconnect/availability, notifications, volume transitions, and related TCP control paths) that this library was extracted from

## License

MIT — see [LICENSE](LICENSE). Copyright holders are listed in [LICENSE](LICENSE).

## Disclaimer

This library is not affiliated with or endorsed by Sony. Use on hardware you own.
Protocol support varies by model and firmware.
