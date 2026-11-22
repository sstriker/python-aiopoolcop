# aiopoolcop

Asynchronous Python client for the [PoolCop](https://www.poolcop.com) Client API
(`https://client-api.poolcop.net`).

It reads pools, devices, live state, settings and history, and sends commands
(pump, pump speed, forced filtration, filtration mode and timers, valve
position, stop backwash, auxiliaries, heating setpoint, jet stream, alarms). All responses are parsed into typed, frozen
dataclasses.

This library backs the [PoolCop Home Assistant integration](https://github.com/sstriker/hass-poolcop).

## Installation

```bash
pip install aiopoolcop
```

Requires Python 3.14 or newer (the same as Home Assistant).

## Getting an API key

The Client API authenticates with an API key tied to your PoolCop account.
Keys for the old PoolCopilot API (poolcopilot.com) do **not** work.

1. Log in at [my.poolcop.com](https://my.poolcop.com) with your PoolCop account.
2. Open **Profile → API key** ([my.poolcop.com/profile/apikey](https://my.poolcop.com/profile/apikey)).
3. Click **Generate a key** and copy it.

One key gives access to every pool and PoolCop your account can see.
Regenerating the key invalidates the old one. Treat the key like a password.

## Usage

```python
import asyncio

from aiopoolcop import PoolCopClientAPI


async def main() -> None:
    async with PoolCopClientAPI(api_key="your-api-key") as api:
        for pool in await api.get_pools():
            print(pool.nickname, pool.city, pool.timezone)

            for minimal in pool.devices:
                device = await api.get_device(minimal.id)
                state = device.state
                print(
                    f"  {device.nickname}: water {state.water_temperature}, "
                    f"pH {state.ph}, ORP {state.orp} mV"
                )
                for pump in state.pumps:
                    print(
                        f"  pump {pump.id}: on={pump.pump_state} "
                        f"speed={pump.current_speed} valve={pump.valve_position}"
                    )


asyncio.run(main())
```

Pass your own `aiohttp.ClientSession` with `session=` to share a session
(the client won't close a session it didn't create).

### Endpoints

| Method | API call |
| --- | --- |
| `get_pools(page=None)` | `GET /pools` |
| `get_pool(pool_id)` | `GET /pools/{id}` |
| `get_devices(page=None)` | `GET /devices` |
| `get_device(device_id)` | `GET /devices/{id}`: state, settings, history, equipment, versions |
| `get_commands(device_id, page=1)` | `GET /devices/{id}/commands` |
| `set_pump(device_id, on=..., pump_id=0)` | `POST .../interactions/pumpstate` |
| `set_pump_speed(device_id, speed)` | `POST .../interactions/pumpspeed` |
| `set_pump_forced(device_id, mode)` | `POST .../interactions/pumpforced` |
| `set_filtration_timer(device_id, mode, timers=None, filtration_id=None)` | `POST .../interactions/filtrationtimer` |
| `set_valve_position(device_id, position)` | `POST .../interactions/valveposition` |
| `stop_backwash(device_id)` | `POST .../interactions/stopbackwash` |
| `set_auxiliary(device_id, module, aux_id, on=...)` | `POST .../interactions/auxstate` |
| `set_heating_setpoint(device_id, setpoint, aux_id, module)` | `POST .../interactions/heatingsetpoint` |
| `set_jet_stream(device_id, on=...)` | `POST .../interactions/jetstreamstate` |
| `clear_alarm(device_id, alarm_code)` | `DELETE .../interactions/clearalarm` |
| `clear_all_alarms(device_id)` | `DELETE .../interactions/clearalarms` |

`get_pools()` and `get_devices()` fetch every page (100 items each, one
request per second) unless you pass `page=`. `get_commands()` returns one
page of the command history, latest first.

### Behaviour of the API to be aware of

- **Rate limits:** at most one request per second per key, and 10 seconds
  between requests on the same entity (pump state, valve position and
  auxiliary state are exempt and allow 1 second). Exceeding them raises
  `PoolCopClientRateLimitError`, which carries `retry_after` when the
  server sends it.
- **Commands are asynchronous:** interaction calls are accepted with HTTP 202
  and can take 30 seconds to 2 minutes to show up in the device state.
- **Units follow your account:** measurements are returned in the units
  selected in your PoolCop app preferences. The API reports them in a
  `units` response header (UCUM codes); the client keeps the latest one in
  `api.units`, e.g. `{"temperature": "Cel", "pressure": "kPa", "volume": "m3",
  "flowRate": "m3/h"}`.

### Errors

All exceptions derive from `PoolCopClientError`:

| Exception | Raised on |
| --- | --- |
| `PoolCopClientAuthError` | HTTP 401/403 (missing or invalid key) |
| `PoolCopClientAccessExpiredError` | HTTP 402 (the device's cloud access has expired) |
| `PoolCopClientNotFoundError` | HTTP 404 |
| `PoolCopClientRateLimitError` | HTTP 429 |
| `PoolCopClientConnectionError` | Timeouts and connection failures |
| `PoolCopClientError` | Anything else, e.g. HTTP 400 (invalid parameters) or 502 (the command failed) |

## API documentation

The official API reference is at
[client-api.poolcop.net/docs](https://client-api.poolcop.net/docs).

## License

Apache-2.0
