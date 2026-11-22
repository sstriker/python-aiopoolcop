"""Asynchronous client for the PoolCop Client API."""

from __future__ import annotations

import asyncio
import contextlib
import socket
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any, Self

from aiohttp.client import ClientError, ClientSession
from yarl import URL

from .const import API_BASE_PATH, API_HOST, USER_AGENT
from .exceptions import (
    PoolCopClientAccessExpiredError,
    PoolCopClientAuthError,
    PoolCopClientConnectionError,
    PoolCopClientError,
    PoolCopClientNotFoundError,
    PoolCopClientRateLimitError,
)
from .models import (
    FiltrationTimer,
    Pool,
    PoolCopCommand,
    PoolCopDevice,
)

# Safety net against a server that keeps reporting hasNextPage.
MAX_PAGES = 100


@dataclass
class PoolCopClientAPI:
    """Asynchronous client for the PoolCop Client API.

    Uses x-api-key header authentication.
    Rate limits: 1s between queries, 10s between queries on same entity.
    Requests made through one client are spaced by ``min_request_interval``.
    """

    api_key: str
    session: ClientSession | None = None
    request_timeout: float = 15.0
    # Minimum seconds between two requests made through this client. The API
    # allows one request per second per key, so share one client per key.
    min_request_interval: float = 1.0

    # Units of the last response, from the ``units`` header, e.g.
    # {"temperature": "Cel", "pressure": "kPa", "volume": "m3",
    #  "flowRate": "m3/h"} (UCUM codes, following the account's preferences).
    units: dict[str, str] = field(default_factory=dict, init=False)

    _close_session: bool = field(default=False, init=False, repr=False)
    _throttle: asyncio.Lock = field(
        default_factory=asyncio.Lock, init=False, repr=False
    )
    _last_request: float | None = field(default=None, init=False, repr=False)

    def _build_url(self, path: str) -> URL:
        """Build a full API URL."""
        return URL.build(
            scheme="https",
            host=API_HOST,
            path=f"{API_BASE_PATH}/{path.lstrip('/')}",
        )

    def _headers(self) -> dict[str, str]:
        """Return request headers."""
        return {
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "x-api-key": self.api_key,
        }

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        return_json: bool = True,
    ) -> Any:
        """Make an API request."""
        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        url = self._build_url(path)
        headers = self._headers()

        try:
            async with self._throttle:
                await self._wait_for_slot()
                try:
                    async with asyncio.timeout(self.request_timeout):
                        response = await self.session.request(
                            method,
                            url,
                            headers=headers,
                            params=params,
                            json=json,
                        )
                finally:
                    self._last_request = time.monotonic()
        except TimeoutError as err:
            msg = "Timeout connecting to PoolCop Client API"
            raise PoolCopClientConnectionError(msg) from err
        except (ClientError, socket.gaierror) as err:
            msg = f"Error connecting to PoolCop Client API: {err}"
            raise PoolCopClientConnectionError(msg) from err

        await self._handle_error_status(response)

        if units := response.headers.get("units"):
            self.units = parse_units(units)

        if not return_json:
            return None

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            text = await response.text()
            msg = f"Unexpected content type: {content_type}: {text}"
            raise PoolCopClientError(msg)

        return await response.json()

    async def _wait_for_slot(self) -> None:
        """Sleep until min_request_interval has passed since the last request."""
        if self._last_request is None or self.min_request_interval <= 0:
            return
        wait = self._last_request + self.min_request_interval - time.monotonic()
        if wait > 0:
            await asyncio.sleep(wait)

    @staticmethod
    async def _handle_error_status(response: Any) -> None:
        """Raise typed exception for error HTTP status codes."""
        status = response.status
        if status < HTTPStatus.BAD_REQUEST:
            return
        if status == HTTPStatus.UNAUTHORIZED or status == HTTPStatus.FORBIDDEN:
            msg = f"Authentication failed ({status})"
            raise PoolCopClientAuthError(msg)
        if status == HTTPStatus.PAYMENT_REQUIRED:
            msg = "The device's cloud access has expired"
            raise PoolCopClientAccessExpiredError(msg)
        if status == HTTPStatus.NOT_FOUND:
            msg = "Resource not found"
            raise PoolCopClientNotFoundError(msg)
        if status == HTTPStatus.TOO_MANY_REQUESTS:
            retry_after = None
            with contextlib.suppress(Exception):
                data = response.headers.get("Retry-After")
                if data:
                    retry_after = int(data)
            msg = "Rate limit exceeded"
            raise PoolCopClientRateLimitError(msg, retry_after=retry_after)
        detail = ""
        with contextlib.suppress(Exception):
            detail = (await response.text()).strip()[:200]
        if status == HTTPStatus.BAD_GATEWAY:
            msg = "The command failed and was not taken into account (502)"
        elif status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            msg = f"Server error ({status})"
        else:
            msg = f"Client error ({status})"
        if detail:
            msg = f"{msg}: {detail}"
        raise PoolCopClientError(msg)

    async def _get_all_pages[T](
        self, path: str, parse: Callable[[dict[str, Any]], T]
    ) -> list[T]:
        """Fetch every page of a paginated endpoint."""
        items: list[T] = []
        page = 1
        while True:
            data = await self._request("GET", path, params={"page": page})
            if not isinstance(data, dict):
                break
            items.extend(parse(item) for item in data.get("data") or [])
            if not data.get("hasNextPage") or page >= MAX_PAGES:
                break
            page += 1
        return items

    async def _get_page[T](
        self, path: str, page: int, parse: Callable[[dict[str, Any]], T]
    ) -> list[T]:
        """Fetch a single page of a paginated endpoint."""
        data = await self._request("GET", path, params={"page": page})
        items = (data.get("data") or []) if isinstance(data, dict) else []
        return [parse(item) for item in items]

    # ------------------------------------------------------------------
    # Pool endpoints
    # ------------------------------------------------------------------

    async def get_pools(self, *, page: int | None = None) -> list[Pool]:
        """Get the pools the API key has access to.

        Fetches every page unless ``page`` is given.
        """
        if page is not None:
            return await self._get_page("/pools", page, Pool.from_dict)
        return await self._get_all_pages("/pools", Pool.from_dict)

    async def get_pool(self, pool_id: int) -> Pool:
        """Get a specific pool by ID."""
        data = await self._request("GET", f"/pools/{pool_id}")
        return Pool.from_dict(data)

    # ------------------------------------------------------------------
    # Device endpoints
    # ------------------------------------------------------------------

    async def get_devices(self, *, page: int | None = None) -> list[PoolCopDevice]:
        """Get the devices the API key has access to.

        Fetches every page unless ``page`` is given.
        """
        if page is not None:
            return await self._get_page("/devices", page, PoolCopDevice.from_dict)
        return await self._get_all_pages("/devices", PoolCopDevice.from_dict)

    async def get_device(self, device_id: int) -> PoolCopDevice:
        """Get a device with full state, settings, history, and equipments."""
        data = await self._request("GET", f"/devices/{device_id}")
        return PoolCopDevice.from_dict(data)

    async def get_commands(
        self, device_id: int, *, page: int = 1
    ) -> list[PoolCopCommand]:
        """Get one page (latest first) of a device's command history."""
        return await self._get_page(
            f"/devices/{device_id}/commands", page, PoolCopCommand.from_dict
        )

    # ------------------------------------------------------------------
    # Device interaction endpoints
    # ------------------------------------------------------------------

    async def set_pump(self, device_id: int, *, on: bool, pump_id: int = 0) -> None:
        """Turn pump on or off."""
        await self._request(
            "POST",
            f"/devices/{device_id}/interactions/pumpstate",
            params={"pumpState": str(on).lower(), "pumpId": pump_id},
            return_json=False,
        )

    async def set_pump_speed(
        self, device_id: int, speed: str, *, pump_id: int = 0
    ) -> None:
        """Set pump speed (None, Speed1-Speed8)."""
        await self._request(
            "POST",
            f"/devices/{device_id}/interactions/pumpspeed",
            params={"speed": speed, "pumpId": pump_id},
            return_json=False,
        )

    async def set_pump_forced(
        self, device_id: int, mode: str, *, pump_id: int = 0
    ) -> None:
        """Set forced filtration mode (NotForced, Forced24H, Forced48H, Forced72H)."""
        await self._request(
            "POST",
            f"/devices/{device_id}/interactions/pumpforced",
            params={"forcedMode": mode, "pumpId": pump_id},
            return_json=False,
        )

    async def set_valve_position(
        self, device_id: int, position: str, *, filter_id: int = 0
    ) -> None:
        """Set valve position (Filter, Waste, Closed, Backwash, Bypass, Rinse)."""
        await self._request(
            "POST",
            f"/devices/{device_id}/interactions/valveposition",
            params={"valvePosition": position, "filterId": filter_id},
            return_json=False,
        )

    async def stop_backwash(self, device_id: int) -> None:
        """Stop a backwash in progress."""
        await self._request(
            "POST",
            f"/devices/{device_id}/interactions/stopbackwash",
            return_json=False,
        )

    async def set_filtration_timer(
        self,
        device_id: int,
        mode: str,
        *,
        timers: Sequence[FiltrationTimer] | None = None,
        filtration_id: int | None = None,
    ) -> None:
        """Set the filtration mode and, optionally, its timers.

        ``mode`` is one of Stop, Timer, EcoPlus, Volume, Continuous, Forced24H,
        Forced48H, Forced72H, Mode24H or NoPump. Without ``filtration_id``
        the first filtration is used.
        """
        params: dict[str, Any] = {"filtrationMode": mode}
        if filtration_id is not None:
            params["filtrationId"] = filtration_id
        await self._request(
            "POST",
            f"/devices/{device_id}/interactions/filtrationtimer",
            params=params,
            json=[t.to_dict() for t in timers] if timers is not None else None,
            return_json=False,
        )

    async def set_auxiliary(
        self,
        device_id: int,
        module: str,
        aux_id: int,
        *,
        on: bool,
    ) -> None:
        """Set an auxiliary output on or off."""
        await self._request(
            "POST",
            f"/devices/{device_id}/interactions/auxstate",
            params={
                "auxState": str(on).lower(),
                "auxId": aux_id,
                "module": module,
            },
            return_json=False,
        )

    async def set_heating_setpoint(
        self,
        device_id: int,
        setpoint: float,
        aux_id: int,
        module: str = "None",
    ) -> None:
        """Set heating setpoint for an auxiliary."""
        await self._request(
            "POST",
            f"/devices/{device_id}/interactions/heatingsetpoint",
            params={
                "heatingSetpoint": setpoint,
                "auxId": aux_id,
                "module": module,
            },
            return_json=False,
        )

    async def set_jet_stream(self, device_id: int, *, on: bool) -> None:
        """Turn the jet stream on or off."""
        await self._request(
            "POST",
            f"/devices/{device_id}/interactions/jetstreamstate",
            params={"jetStreamState": str(on).lower()},
            return_json=False,
        )

    async def clear_alarm(self, device_id: int, alarm_code: str) -> None:
        """Clear a specific alarm by code."""
        await self._request(
            "DELETE",
            f"/devices/{device_id}/interactions/clearalarm",
            params={"alarmCode": alarm_code},
            return_json=False,
        )

    async def clear_all_alarms(self, device_id: int) -> None:
        """Clear all active alarms."""
        await self._request(
            "DELETE",
            f"/devices/{device_id}/interactions/clearalarms",
            return_json=False,
        )

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close the client session if we created it."""
        if self.session and self._close_session:
            await self.session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *_exc_info: Any) -> None:
        await self.close()


def parse_units(header: str) -> dict[str, str]:
    """Parse a ``units`` header such as ``temperature=Cel,pressure=kPa``."""
    units: dict[str, str] = {}
    for part in header.split(","):
        key, sep, value = part.partition("=")
        if sep and key.strip():
            units[key.strip()] = value.strip()
    return units


# Backwards-compatible alias
PoolCopCloudAPI = PoolCopClientAPI
