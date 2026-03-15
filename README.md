# aiopoolcop

Asynchronous Python client for the PoolCop Cloud API.

## Installation

```bash
pip install aiopoolcop
```

## Usage

```python
import asyncio
from aiopoolcop import PoolCopCloudAPI

async def main():
    async with PoolCopCloudAPI(token="your-oauth2-token") as api:
        devices = await api.get_poolcops()
        for device in devices:
            print(f"{device.nickname} (connected: {device.is_connected})")

        state = await api.get_state(devices[0].id)
        print(f"Water temp: {state.water_temperature}°C")
        print(f"pH: {state.ph}")
        print(f"ORP: {state.orp} mV")

asyncio.run(main())
```

## License

Apache-2.0
