"""Asynchronous client for the PoolCop Cloud API."""

from __future__ import annotations

import asyncio
import contextlib
import socket
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import Any, Self, cast

from aiohttp.client import ClientError, ClientResponseError, ClientSession
from yarl import URL

from .auth import TokenManager
from .const import API_BASE_PATH, API_HOST, USER_AGENT
from .exceptions import (
    PoolCopCloudAuthError,
    PoolCopCloudConnectionError,
    PoolCopCloudError,
    PoolCopCloudNotFoundError,
    PoolCopCloudRateLimitError,
)
from .models import (
    Pool,
    PoolCopAlarm,
    PoolCopAuxiliary,
    PoolCopCommand,
    PoolCopDevice,
    PoolCopState,
    PoolCopSummary,
    UserProfile,
)


@dataclass
class PoolCopCloudAPI:
    """Main class for interacting with the PoolCop Cloud API."""

    token: str
    session: ClientSession | None = None
    request_timeout: float = 15.0
    token_refresh_callback: Any = None
    lang: str | None = None

    _close_session: bool = field(default=False, init=False, repr=False)
    _token_manager: TokenManager = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._token_manager = TokenManager(
            token=self.token,
            token_refresh_callback=self.token_refresh_callback,
        )

    def _build_url(self, path: str) -> URL:
        return URL.build(
            scheme="https",
            host=API_HOST,
            path=f"{API_BASE_PATH}/{path}",
        )

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
            "Authorization": f"Bearer {self._token_manager.token}",
        }
        if self.lang is not None:
            headers["Accept-Language"] = self.lang
        return headers

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        return_json: bool = True,
    ) -> Any:
        """Make a request to the PoolCop Cloud API.

        Handles 401 retry via token refresh, 429 rate limiting,
        and maps HTTP errors to typed exceptions.
        """
        if self.session is None:
            self.session = ClientSession()
            self._close_session = True

        url = self._build_url(path)
        response = await self._do_request(
            method, url, json_data=json_data, params=params
        )

        if response.status == HTTPStatus.UNAUTHORIZED:
            try:
                await self._token_manager.refresh()
            except RuntimeError as exc:
                raise PoolCopCloudAuthError(
                    "Authentication failed and no refresh callback available."
                ) from exc
            response = await self._do_request(
                method, url, json_data=json_data, params=params
            )
            if response.status == HTTPStatus.UNAUTHORIZED:
                raise PoolCopCloudAuthError(
                    "Authentication failed after token refresh."
                )

        self._handle_error_status(response)

        if not return_json:
            return None

        content_type = response.headers.get("Content-Type", "")
        if "application/json" not in content_type:
            text = await response.text()
            msg = "Unexpected content type from the PoolCop Cloud API"
            raise PoolCopCloudError(
                msg,
                {"Content-Type": content_type, "response": text},
            )

        return cast(Any, await response.json())

    async def _do_request(
        self,
        method: str,
        url: URL,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Execute a single HTTP request with error handling."""
        assert self.session is not None  # noqa: S101

        try:
            async with asyncio.timeout(self.request_timeout):
                return await self.session.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json_data,
                    params=params,
                    ssl=True,
                )
        except TimeoutError as exception:
            msg = "Timeout occurred while connecting to the PoolCop Cloud API."
            raise PoolCopCloudConnectionError(msg) from exception
        except (ClientError, socket.gaierror) as exception:
            msg = "Error occurred while communicating with the PoolCop Cloud API."
            raise PoolCopCloudConnectionError(msg) from exception

    @staticmethod
    def _handle_error_status(response: Any) -> None:
        """Raise typed exceptions for error HTTP status codes."""
        status = response.status
        if status == HTTPStatus.UNAUTHORIZED or status == HTTPStatus.FORBIDDEN:
            raise PoolCopCloudAuthError(
                f"Authentication/authorization failed (HTTP {status})."
            )
        if status == HTTPStatus.NOT_FOUND:
            raise PoolCopCloudNotFoundError("Resource not found (HTTP 404).")
        if status == HTTPStatus.TOO_MANY_REQUESTS:
            retry_after = None
            raw = response.headers.get("Retry-After")
            if raw is not None:
                with contextlib.suppress(ValueError, TypeError):
                    retry_after = int(raw)
            raise PoolCopCloudRateLimitError(
                "Rate limit exceeded (HTTP 429).", retry_after=retry_after
            )
        if status >= HTTPStatus.BAD_REQUEST:
            try:
                response.raise_for_status()
            except ClientResponseError as exc:
                raise PoolCopCloudError(
                    f"API returned HTTP {status}: {exc.message}"
                ) from exc

    # ------------------------------------------------------------------
    # Phase 1: Core endpoints
    # ------------------------------------------------------------------

    async def get_poolcops(self) -> list[PoolCopSummary]:
        """Get all PoolCop devices for the current user."""
        data = await self._request("GET", "poolcops")
        if isinstance(data, list):
            return [PoolCopSummary.from_dict(d) for d in data]
        return []

    async def get_poolcop(self, poolcop_id: int) -> PoolCopDevice:
        """Get a specific PoolCop device with full state."""
        data = await self._request("GET", f"poolcops/{poolcop_id}")
        return PoolCopDevice.from_dict(data)

    async def get_state(self, poolcop_id: int) -> PoolCopState:
        """Get the current state of a PoolCop device."""
        data = await self._request("GET", f"poolcops/{poolcop_id}/state")
        return PoolCopState.from_dict(data)

    async def get_alarms(self, poolcop_id: int) -> list[PoolCopAlarm]:
        """Get current alarms for a PoolCop device."""
        data = await self._request("GET", f"poolcops/{poolcop_id}/alarms")
        if isinstance(data, list):
            return [PoolCopAlarm.from_dict(d) for d in data]
        return []

    async def get_alarm(self, poolcop_id: int, code: str) -> PoolCopAlarm:
        """Get a specific alarm by code."""
        data = await self._request("GET", f"poolcops/{poolcop_id}/alarms/{code}")
        return PoolCopAlarm.from_dict(data)

    async def clear_alarm(self, poolcop_id: int, code: str) -> PoolCopCommand:
        """Clear a specific alarm by code."""
        data = await self._request("DELETE", f"poolcops/{poolcop_id}/alarms/{code}")
        return PoolCopCommand.from_dict(data)

    async def get_alarm_history(
        self,
        poolcop_id: int,
        *,
        start: str | None = None,
        end: str | None = None,
    ) -> list[PoolCopAlarm]:
        """Get alarm history for a PoolCop device."""
        params: dict[str, Any] = {}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        data = await self._request(
            "GET",
            f"poolcops/{poolcop_id}/alarms/history",
            params=params if params else None,
        )
        if isinstance(data, list):
            return [PoolCopAlarm.from_dict(d) for d in data]
        return []

    async def set_pump(self, poolcop_id: int, *, on: bool) -> PoolCopCommand:
        """Turn the pump on or off."""
        data = await self._request(
            "POST",
            f"poolcops/{poolcop_id}/state/pump",
            json_data={"pumpState": on},
        )
        return PoolCopCommand.from_dict(data)

    async def set_pump_speed(self, poolcop_id: int, speed: str) -> PoolCopCommand:
        """Set the pump speed (e.g. 'Speed1'..'Speed8')."""
        data = await self._request(
            "POST",
            f"poolcops/{poolcop_id}/state/pump/speed",
            json_data={"pumpSpeed": speed},
        )
        return PoolCopCommand.from_dict(data)

    async def set_pump_forced(self, poolcop_id: int, mode: str) -> PoolCopCommand:
        """Set forced pump mode (e.g. 'NotForced', 'Forced24H', etc.)."""
        data = await self._request(
            "POST",
            f"poolcops/{poolcop_id}/state/pump/forced",
            json_data={"forcedPumpMode": mode},
        )
        return PoolCopCommand.from_dict(data)

    async def set_valve_position(
        self, poolcop_id: int, position: str
    ) -> PoolCopCommand:
        """Set the valve position (e.g. 'Filter', 'Waste', etc.)."""
        data = await self._request(
            "POST",
            f"poolcops/{poolcop_id}/state/valve",
            json_data={"valvePosition": position},
        )
        return PoolCopCommand.from_dict(data)

    async def set_auxiliary(
        self,
        poolcop_id: int,
        module: str,
        aux: str,
        *,
        on: bool,
    ) -> PoolCopCommand:
        """Set an auxiliary port on or off."""
        data = await self._request(
            "POST",
            f"poolcops/{poolcop_id}/state/aux/{module}/{aux}",
            json_data={"status": on},
        )
        return PoolCopCommand.from_dict(data)

    async def get_auxiliaries(self, poolcop_id: int) -> list[PoolCopAuxiliary]:
        """Get auxiliary port configurations."""
        data = await self._request("GET", f"poolcops/{poolcop_id}/state/aux")
        if isinstance(data, list):
            return [PoolCopAuxiliary.from_dict(d) for d in data]
        return []

    async def trigger_backwash(self, poolcop_id: int) -> PoolCopCommand:
        """Trigger a backwash cycle."""
        data = await self._request(
            "POST", f"poolcops/{poolcop_id}/state/filter/backwash"
        )
        return PoolCopCommand.from_dict(data)

    async def trigger_ph_measure(self, poolcop_id: int) -> PoolCopCommand:
        """Trigger a pH measurement."""
        data = await self._request("POST", f"poolcops/{poolcop_id}/state/pH/measure")
        return PoolCopCommand.from_dict(data)

    async def trigger_orp_measure(self, poolcop_id: int) -> PoolCopCommand:
        """Trigger an ORP measurement."""
        data = await self._request("POST", f"poolcops/{poolcop_id}/state/ORP/measure")
        return PoolCopCommand.from_dict(data)

    async def set_water_valve(self, poolcop_id: int, *, on: bool) -> PoolCopCommand:
        """Open or close the water level valve."""
        data = await self._request(
            "POST",
            f"poolcops/{poolcop_id}/state/waterlevel/valve",
            json_data={"waterLevelValve": "Open" if on else "Close"},
        )
        return PoolCopCommand.from_dict(data)

    async def get_commands(self, poolcop_id: int) -> list[PoolCopCommand]:
        """Get commands sent to a PoolCop device."""
        data = await self._request("GET", f"poolcops/{poolcop_id}/commands")
        if isinstance(data, list):
            return [PoolCopCommand.from_dict(d) for d in data]
        return []

    async def get_pools(self) -> list[Pool]:
        """Get all pools for the current user."""
        data = await self._request("GET", "pools")
        if isinstance(data, list):
            return [Pool.from_dict(d) for d in data]
        return []

    async def get_pool(self, pool_id: int) -> Pool:
        """Get a specific pool."""
        data = await self._request("GET", f"pools/{pool_id}")
        return Pool.from_dict(data)

    async def get_profile(self) -> UserProfile:
        """Get the authenticated user's profile."""
        data = await self._request("GET", "profile")
        return UserProfile.from_dict(data)

    # ------------------------------------------------------------------
    # Session management
    # ------------------------------------------------------------------

    async def close(self) -> None:
        """Close open client session."""
        if self.session and self._close_session:
            await self.session.close()
            self.session = None

    async def __aenter__(self) -> Self:
        """Async enter."""
        return self

    async def __aexit__(self, *_exc_info: Any) -> None:
        """Async exit."""
        await self.close()
