"""Asynchronous client for the PoolCop Client API."""

from __future__ import annotations

import asyncio
import contextlib
import socket
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any, Self

from aiohttp.client import ClientError, ClientSession
from yarl import URL

from .const import API_BASE_PATH, API_HOST, USER_AGENT
from .exceptions import (
    PoolCopClientAuthError,
    PoolCopClientConnectionError,
    PoolCopClientError,
    PoolCopClientNotFoundError,
    PoolCopClientRateLimitError,
)
from .models import (
    Pool,
    PoolCopCommand,
    PoolCopDevice,
)


@dataclass
class PoolCopClientAPI:
    """Asynchronous client for the PoolCop Client API.

    Uses x-api-key header authentication.
    Rate limits: 1s between queries, 10s between queries on same entity.
    """

    api_key: str
    session: ClientSession | None = None
    request_timeout: float = 15.0

    _close_session: bool = field(default=False, init=False, repr=False)

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
        return_json: bool = True,
    ) -> Any:
        """Make an API request."""
        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        url = self._build_url(path)
        headers = self._headers()

        try:
            async with asyncio.timeout(self.request_timeout):
                response = await self.session.request(
                    method,
                    url,
                    headers=headers,
                    params=params,
                )
        except asyncio.TimeoutError as err:
            msg = "Timeout connecting to PoolCop Client API"
            raise PoolCopClientConnectionError(msg) from err
        except (ClientError, socket.gaierror) as err:
            msg = f"Error connecting to PoolCop Client API: {err}"
            raise PoolCopClientConnectionError(msg) from err

        self._handle_error_status(response)

        if not return_json:
            return None

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            text = await response.text()
            msg = f"Unexpected content type: {content_type}: {text}"
            raise PoolCopClientError(msg)

        return await response.json()

    @staticmethod
    def _handle_error_status(response: Any) -> None:
        """Raise typed exception for error HTTP status codes."""
        status = response.status
        if status == HTTPStatus.UNAUTHORIZED or status == HTTPStatus.FORBIDDEN:
            msg = f"Authentication failed ({status})"
            raise PoolCopClientAuthError(msg)
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
        if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            msg = f"Server error ({status})"
            raise PoolCopClientError(msg)
        if status >= HTTPStatus.BAD_REQUEST:
            msg = f"Client error ({status})"
            raise PoolCopClientError(msg)

    # ------------------------------------------------------------------
    # Pool endpoints
    # ------------------------------------------------------------------

    async def get_pools(self) -> list[Pool]:
        """Get all pools the API key has access to."""
        data = await self._request("GET", "/pools")
        # Paginated response: {data: [...], currentPage, totalPages, ...}
        items = data.get("data", []) if isinstance(data, dict) else []
        return [Pool.from_dict(p) for p in items]

    async def get_pool(self, pool_id: int) -> Pool:
        """Get a specific pool by ID."""
        data = await self._request("GET", f"/pools/{pool_id}")
        return Pool.from_dict(data)

    # ------------------------------------------------------------------
    # Device endpoints
    # ------------------------------------------------------------------

    async def get_device(self, device_id: int) -> PoolCopDevice:
        """Get a device with full state, settings, history, and equipments."""
        data = await self._request("GET", f"/devices/{device_id}")
        return PoolCopDevice.from_dict(data)

    async def get_commands(self, device_id: int) -> list[PoolCopCommand]:
        """Get command history for a device."""
        data = await self._request("GET", f"/devices/{device_id}/commands")
        items = data.get("data", []) if isinstance(data, dict) else []
        return [PoolCopCommand.from_dict(c) for c in items]

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


# Backwards-compatible alias
PoolCopCloudAPI = PoolCopClientAPI
