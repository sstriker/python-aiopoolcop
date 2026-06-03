"""Tests for the PoolCop Client API client."""

import re
import socket

import pytest
from aiohttp import ClientError
from aioresponses import aioresponses

from aiopoolcop import (
    PoolCopClientAPI,
    PoolCopClientAuthError,
    PoolCopClientConnectionError,
    PoolCopClientError,
    PoolCopClientNotFoundError,
    PoolCopClientRateLimitError,
)

from .conftest import (
    BASE_URL,
    COMMANDS_RESPONSE,
    DEVICE_RESPONSE,
    POOL_RESPONSE,
    POOLS_RESPONSE,
)

URL_PATTERN = re.compile(rf"^{re.escape(BASE_URL)}/.*$")


# ---------------------------------------------------------------------------
# Connection & error handling
# ---------------------------------------------------------------------------


class TestErrorHandling:
    """Test HTTP error handling."""

    async def test_timeout(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.get(URL_PATTERN, timeout=True)
        with pytest.raises(PoolCopClientConnectionError):
            await api.get_pools()

    async def test_client_error(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.get(URL_PATTERN, exception=ClientError())
        with pytest.raises(PoolCopClientConnectionError):
            await api.get_pools()

    async def test_dns_error(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.get(URL_PATTERN, exception=socket.gaierror())
        with pytest.raises(PoolCopClientConnectionError):
            await api.get_pools()

    async def test_401_auth_error(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.get(URL_PATTERN, status=401)
        with pytest.raises(PoolCopClientAuthError):
            await api.get_pools()

    async def test_403_auth_error(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.get(URL_PATTERN, status=403)
        with pytest.raises(PoolCopClientAuthError):
            await api.get_pools()

    async def test_404_not_found(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.get(URL_PATTERN, status=404)
        with pytest.raises(PoolCopClientNotFoundError):
            await api.get_device(9999)

    async def test_429_rate_limit(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.get(
            URL_PATTERN,
            status=429,
            headers={"Retry-After": "10"},
        )
        with pytest.raises(PoolCopClientRateLimitError) as exc_info:
            await api.get_pools()
        assert exc_info.value.retry_after == 10

    async def test_500_server_error(
        self, api: PoolCopClientAPI, mock_api: aioresponses
    ):
        mock_api.get(URL_PATTERN, status=500)
        with pytest.raises(PoolCopClientError):
            await api.get_pools()

    async def test_non_json_response(
        self, api: PoolCopClientAPI, mock_api: aioresponses
    ):
        mock_api.get(
            URL_PATTERN,
            body="not json",
            content_type="text/plain",
        )
        with pytest.raises(PoolCopClientError, match="Unexpected content type"):
            await api.get_pools()


# ---------------------------------------------------------------------------
# Session management
# ---------------------------------------------------------------------------


class TestSession:
    """Test session lifecycle."""

    async def test_creates_session_if_none(self, mock_api: aioresponses):
        api = PoolCopClientAPI(api_key="test-key")
        mock_api.get(URL_PATTERN, payload=POOLS_RESPONSE)
        await api.get_pools()
        assert api.session is not None
        await api.close()

    async def test_api_key_in_headers(
        self, api: PoolCopClientAPI, mock_api: aioresponses
    ):
        mock_api.get(URL_PATTERN, payload=POOLS_RESPONSE)
        await api.get_pools()
        # Find the request that was made and check headers
        for key, calls in mock_api.requests.items():
            if key[0] == "GET":
                assert calls[0].kwargs["headers"]["x-api-key"] == "test-api-key"
                break
        else:
            pytest.fail("No GET request found")

    async def test_context_manager(self, mock_api: aioresponses):
        mock_api.get(URL_PATTERN, payload=POOLS_RESPONSE)
        async with PoolCopClientAPI(api_key="test-key") as api:
            await api.get_pools()
            assert api.session is not None


# ---------------------------------------------------------------------------
# Pool endpoints
# ---------------------------------------------------------------------------


class TestPools:
    """Test pool endpoints."""

    async def test_get_pools(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.get(f"{BASE_URL}/pools", payload=POOLS_RESPONSE)
        pools = await api.get_pools()
        assert len(pools) == 1
        assert pools[0].id == 97138
        assert pools[0].nickname == "Striker"
        assert pools[0].latitude == 52.165958
        assert len(pools[0].devices) == 1
        assert pools[0].devices[0].id == 2478

    async def test_get_pool(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.get(f"{BASE_URL}/pools/97138", payload=POOL_RESPONSE)
        pool = await api.get_pool(97138)
        assert pool.id == 97138
        assert pool.city == "TestCity"
        assert pool.timezone == "Europe/Amsterdam"


# ---------------------------------------------------------------------------
# Device endpoints
# ---------------------------------------------------------------------------


class TestDevice:
    """Test device endpoints."""

    async def test_get_devices(self, api: PoolCopClientAPI, mock_api: aioresponses):
        paginated = {
            "currentPage": 1,
            "pageSize": 100,
            "totalCount": 1,
            "totalPages": 1,
            "hasPreviousPage": False,
            "hasNextPage": False,
            "data": [DEVICE_RESPONSE],
        }
        mock_api.get(
            re.compile(rf"{re.escape(BASE_URL)}/devices(\?.*)?$"),
            payload=paginated,
        )
        devices = await api.get_devices()
        assert len(devices) == 1
        assert devices[0].id == 2478

    async def test_get_device(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.get(f"{BASE_URL}/devices/2478", payload=DEVICE_RESPONSE)
        device = await api.get_device(2478)
        assert device.id == 2478
        assert device.nickname == "Striker"
        assert device.is_fully_connected is True

        # State
        assert device.state.ph == 7.5
        assert device.state.orp == 810
        assert device.state.water_temperature == 27.2
        assert device.state.mains_voltage == 187
        assert device.state.service_mode is False
        assert device.state.ph_dosing is False
        assert device.state.alarms == ["PressureLowPump1"]

        # Pumps
        assert len(device.state.pumps) == 1
        pump = device.state.pumps[0]
        assert pump.running_status == "TimerMode"
        assert pump.filtration_mode == "Timer"
        assert pump.number_of_speeds == "Speed3"
        assert pump.pump_state is True
        assert pump.current_speed == "Speed1"
        assert pump.pressure == 76.5

        # Settings
        assert device.settings.pool.volume == 77
        assert device.settings.pool.type == "RimflowTypeB"
        assert device.settings.ph.set_point == 7.5
        assert device.settings.ph.mode == "phMinus"
        assert device.settings.disinfection.orp.set_point == 770
        assert len(device.settings.filtrations) == 1
        assert len(device.settings.filtrations[0].timers) == 2
        assert device.settings.filtrations[0].pump_type == "BaduEcoTouch"

        # Aux settings
        assert len(device.settings.auxs) == 1
        assert device.settings.auxs[0].label == "TransferPump"
        assert device.settings.auxs[0].friendly_name == "Apf"

        # Equipments
        assert device.equipments_info.has_ph_sensor is True
        assert device.equipments_info.has_jet_stream is False

        # History
        assert device.history.last_backwash_date == "2026-05-16T11:03:00"

        # Version
        assert device.version_info.poolcop_version == "44.9.0"
        assert device.version_info.model == "Evolution"

    async def test_get_commands(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.get(f"{BASE_URL}/devices/2478/commands", payload=COMMANDS_RESPONSE)
        commands = await api.get_commands(2478)
        assert len(commands) == 1
        assert commands[0].id == 7779477
        assert commands[0].user == "Test User"
        assert commands[0].is_delivered is True


# ---------------------------------------------------------------------------
# Interaction endpoints
# ---------------------------------------------------------------------------


class TestInteractions:
    """Test device interaction endpoints."""

    async def test_set_pump(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.post(
            re.compile(rf"{re.escape(BASE_URL)}/devices/2478/interactions/pumpstate"),
            status=202,
        )
        await api.set_pump(2478, on=True)

    async def test_set_pump_speed(
        self, api: PoolCopClientAPI, mock_api: aioresponses
    ):
        mock_api.post(
            re.compile(rf"{re.escape(BASE_URL)}/devices/2478/interactions/pumpspeed"),
            status=202,
        )
        await api.set_pump_speed(2478, "Speed2")

    async def test_set_pump_forced(
        self, api: PoolCopClientAPI, mock_api: aioresponses
    ):
        mock_api.post(
            re.compile(
                rf"{re.escape(BASE_URL)}/devices/2478/interactions/pumpforced"
            ),
            status=202,
        )
        await api.set_pump_forced(2478, "Forced24H")

    async def test_set_valve_position(
        self, api: PoolCopClientAPI, mock_api: aioresponses
    ):
        mock_api.post(
            re.compile(
                rf"{re.escape(BASE_URL)}/devices/2478/interactions/valveposition"
            ),
            status=202,
        )
        await api.set_valve_position(2478, "Backwash")

    async def test_set_auxiliary(
        self, api: PoolCopClientAPI, mock_api: aioresponses
    ):
        mock_api.post(
            re.compile(rf"{re.escape(BASE_URL)}/devices/2478/interactions/auxstate"),
            status=202,
        )
        await api.set_auxiliary(2478, "None", 4, on=True)

    async def test_set_heating_setpoint(
        self, api: PoolCopClientAPI, mock_api: aioresponses
    ):
        mock_api.post(
            re.compile(
                rf"{re.escape(BASE_URL)}/devices/2478/interactions/heatingsetpoint"
            ),
            status=202,
        )
        await api.set_heating_setpoint(2478, 28.5, aux_id=4)

    async def test_set_jet_stream(
        self, api: PoolCopClientAPI, mock_api: aioresponses
    ):
        mock_api.post(
            re.compile(
                rf"{re.escape(BASE_URL)}/devices/2478/interactions/jetstreamstate"
            ),
            status=202,
        )
        await api.set_jet_stream(2478, on=True)

    async def test_clear_alarm(self, api: PoolCopClientAPI, mock_api: aioresponses):
        mock_api.delete(
            re.compile(rf"{re.escape(BASE_URL)}/devices/2478/interactions/clearalarm"),
            status=202,
        )
        await api.clear_alarm(2478, "PressureLowPump1")

    async def test_clear_all_alarms(
        self, api: PoolCopClientAPI, mock_api: aioresponses
    ):
        mock_api.delete(
            re.compile(
                rf"{re.escape(BASE_URL)}/devices/2478/interactions/clearalarms"
            ),
            status=202,
        )
        await api.clear_all_alarms(2478)


# ---------------------------------------------------------------------------
# Backwards compatibility
# ---------------------------------------------------------------------------


class TestCompat:
    """Test backwards-compatible aliases."""

    def test_cloud_api_alias(self):
        from aiopoolcop import PoolCopCloudAPI

        assert PoolCopCloudAPI is PoolCopClientAPI

    def test_cloud_exception_aliases(self):
        from aiopoolcop import (
            PoolCopCloudAuthError,
            PoolCopCloudConnectionError,
            PoolCopCloudError,
            PoolCopCloudNotFoundError,
            PoolCopCloudRateLimitError,
        )

        assert PoolCopCloudError is PoolCopClientError
        assert PoolCopCloudAuthError is PoolCopClientAuthError
        assert PoolCopCloudConnectionError is PoolCopClientConnectionError
        assert PoolCopCloudNotFoundError is PoolCopClientNotFoundError
        assert PoolCopCloudRateLimitError is PoolCopClientRateLimitError
