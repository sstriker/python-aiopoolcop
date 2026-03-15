"""Tests for the PoolCop Cloud API client."""

import re
import socket

import pytest
from aiohttp import ClientError, ClientSession

from aiopoolcop import (
    PoolCopCloudAPI,
    PoolCopCloudAuthError,
    PoolCopCloudConnectionError,
    PoolCopCloudError,
    PoolCopCloudNotFoundError,
    PoolCopCloudRateLimitError,
)

from .conftest import (
    ALARM_HISTORY_RESPONSE,
    ALARM_RESPONSE,
    AUX_RESPONSE,
    BASE_URL,
    COMMAND_RESPONSE,
    POOL_RESPONSE,
    POOLCOP_RESPONSE,
    PROFILE_RESPONSE,
    STATE_RESPONSE,
    WEATHER_RESPONSE,
)

# ------------------------------------------------------------------
# Connection / error handling
# ------------------------------------------------------------------


async def test_timeout_error(api, mock_api):
    """TimeoutError raises PoolCopCloudConnectionError."""
    mock_api.get(f"{BASE_URL}/poolcops", exception=TimeoutError())

    async with api:
        with pytest.raises(PoolCopCloudConnectionError, match="Timeout"):
            await api.get_poolcops()


async def test_client_error(api, mock_api):
    """ClientError raises PoolCopCloudConnectionError."""
    mock_api.get(f"{BASE_URL}/poolcops", exception=ClientError("conn refused"))

    async with api:
        with pytest.raises(PoolCopCloudConnectionError):
            await api.get_poolcops()


async def test_dns_error(api, mock_api):
    """socket.gaierror raises PoolCopCloudConnectionError."""
    mock_api.get(f"{BASE_URL}/poolcops", exception=socket.gaierror("DNS failure"))

    async with api:
        with pytest.raises(PoolCopCloudConnectionError):
            await api.get_poolcops()


async def test_auth_error_401(api, mock_api):
    """HTTP 401 without refresh callback raises PoolCopCloudAuthError."""
    mock_api.get(f"{BASE_URL}/poolcops", status=401)

    async with api:
        with pytest.raises(PoolCopCloudAuthError):
            await api.get_poolcops()


async def test_auth_error_403(api, mock_api):
    """HTTP 403 raises PoolCopCloudAuthError."""
    mock_api.get(f"{BASE_URL}/poolcops", status=403)

    async with api:
        with pytest.raises(PoolCopCloudAuthError):
            await api.get_poolcops()


async def test_not_found_404(api, mock_api):
    """HTTP 404 raises PoolCopCloudNotFoundError."""
    mock_api.get(f"{BASE_URL}/poolcops/999", status=404)

    async with api:
        with pytest.raises(PoolCopCloudNotFoundError):
            await api.get_poolcop(999)


async def test_rate_limit_429(api, mock_api):
    """HTTP 429 raises PoolCopCloudRateLimitError."""
    mock_api.get(
        f"{BASE_URL}/poolcops",
        status=429,
        headers={"Retry-After": "60"},
    )

    async with api:
        with pytest.raises(PoolCopCloudRateLimitError) as exc_info:
            await api.get_poolcops()
        assert exc_info.value.retry_after == 60


async def test_rate_limit_429_no_retry_after(api, mock_api):
    """HTTP 429 without Retry-After header."""
    mock_api.get(f"{BASE_URL}/poolcops", status=429)

    async with api:
        with pytest.raises(PoolCopCloudRateLimitError) as exc_info:
            await api.get_poolcops()
        assert exc_info.value.retry_after is None


async def test_server_error_500(api, mock_api):
    """HTTP 500 raises PoolCopCloudError."""
    mock_api.get(f"{BASE_URL}/poolcops", status=500)

    async with api:
        with pytest.raises(PoolCopCloudError):
            await api.get_poolcops()


async def test_non_json_content_type(api, mock_api):
    """Non-JSON content type raises PoolCopCloudError."""
    mock_api.get(
        f"{BASE_URL}/poolcops",
        body="<html>Error</html>",
        content_type="text/html",
    )

    async with api:
        with pytest.raises(PoolCopCloudError, match="Unexpected content type"):
            await api.get_poolcops()


# ------------------------------------------------------------------
# Token refresh
# ------------------------------------------------------------------


async def test_token_refresh_on_401(mock_api):
    """401 triggers token refresh and retries."""

    async def _refresh() -> str:
        return "refreshed-token"

    api = PoolCopCloudAPI(token="expired", token_refresh_callback=_refresh)

    # First request returns 401, second succeeds
    mock_api.get(f"{BASE_URL}/poolcops", status=401)
    mock_api.get(f"{BASE_URL}/poolcops", payload=[])

    async with api:
        result = await api.get_poolcops()
    assert result == []


async def test_token_refresh_fails_again(mock_api):
    """401 after refresh raises PoolCopCloudAuthError."""

    async def _refresh() -> str:
        return "still-bad"

    api = PoolCopCloudAPI(token="expired", token_refresh_callback=_refresh)

    mock_api.get(f"{BASE_URL}/poolcops", status=401)
    mock_api.get(f"{BASE_URL}/poolcops", status=401)

    async with api:
        with pytest.raises(PoolCopCloudAuthError, match="after token refresh"):
            await api.get_poolcops()


# ------------------------------------------------------------------
# Session management
# ------------------------------------------------------------------


async def test_self_created_session_closed(mock_api):
    """Session created by client is closed on exit."""
    api = PoolCopCloudAPI(token="test")
    mock_api.get(f"{BASE_URL}/poolcops", payload=[])

    async with api:
        await api.get_poolcops()

    assert api.session is None


async def test_provided_session_not_closed(mock_api):
    """User-provided session is not closed."""
    session = ClientSession()
    api = PoolCopCloudAPI(token="test", session=session)
    mock_api.get(f"{BASE_URL}/poolcops", payload=[])

    async with api:
        await api.get_poolcops()

    assert not session.closed
    await session.close()


async def test_lang_header(mock_api):
    """Accept-Language header is set when lang is configured."""
    api = PoolCopCloudAPI(token="test", lang="fr-FR")
    headers = api._headers()
    assert headers["Accept-Language"] == "fr-FR"


async def test_no_lang_header_by_default(api):
    """Accept-Language header is not set by default."""
    headers = api._headers()
    assert "Accept-Language" not in headers


async def test_bearer_token_in_header(api):
    """Authorization header contains Bearer token."""
    headers = api._headers()
    assert headers["Authorization"] == "Bearer test-token-123"


# ------------------------------------------------------------------
# Phase 1: Core endpoints
# ------------------------------------------------------------------


async def test_get_poolcops(api, mock_api):
    """Get list of PoolCop devices."""
    mock_api.get(
        f"{BASE_URL}/poolcops",
        payload=[{"id": 42, "nickname": "My PoolCop", "isConnected": True}],
    )

    async with api:
        result = await api.get_poolcops()

    assert len(result) == 1
    assert result[0].id == 42
    assert result[0].nickname == "My PoolCop"


async def test_get_poolcops_empty(api, mock_api):
    """Get empty list of PoolCop devices."""
    mock_api.get(f"{BASE_URL}/poolcops", payload=[])

    async with api:
        result = await api.get_poolcops()

    assert result == []


async def test_get_poolcop(api, mock_api):
    """Get single PoolCop device with state."""
    mock_api.get(f"{BASE_URL}/poolcops/42", payload=POOLCOP_RESPONSE)

    async with api:
        device = await api.get_poolcop(42)

    assert device.id == 42
    assert device.nickname == "My PoolCop"
    assert device.is_connected is True
    assert device.state.ph == 7.2
    assert device.state.orp == 650
    assert len(device.state.pumps) == 1
    assert device.state.pumps[0].current_speed == "Speed2"


async def test_get_state(api, mock_api):
    """Get device state."""
    mock_api.get(f"{BASE_URL}/poolcops/42/state", payload=STATE_RESPONSE)

    async with api:
        state = await api.get_state(42)

    assert state.status == "Ready"
    assert state.water_temperature == 26.5
    assert state.water_level.installed is True
    assert state.water_level.state == "Normal"
    assert state.pool_cover.installed is True
    assert state.jet_stream.installed is True
    assert len(state.flow_vis) == 1
    assert state.inputs["Input1"] is True


async def test_get_alarms(api, mock_api):
    """Get active alarms."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/alarms",
        payload=[ALARM_RESPONSE],
    )

    async with api:
        alarms = await api.get_alarms(42)

    assert len(alarms) == 1
    assert alarms[0].code == "A001"
    assert alarms[0].is_active is True


async def test_get_alarm(api, mock_api):
    """Get a specific alarm by code."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/alarms/A001",
        payload=ALARM_RESPONSE,
    )

    async with api:
        alarm = await api.get_alarm(42, "A001")

    assert alarm.code == "A001"
    assert alarm.severity == "Warning"


async def test_clear_alarm(api, mock_api):
    """Clear a specific alarm."""
    mock_api.delete(
        f"{BASE_URL}/poolcops/42/alarms/A001",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.clear_alarm(42, "A001")

    assert cmd.id == 1001


async def test_get_alarm_history(api, mock_api):
    """Get alarm history."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/alarms/history",
        payload=[ALARM_HISTORY_RESPONSE],
    )

    async with api:
        history = await api.get_alarm_history(42)

    assert len(history) == 1
    assert history[0].code == "A002"
    assert history[0].is_active is False


async def test_get_alarm_history_with_dates(api, mock_api):
    """Get alarm history with date filters."""
    mock_api.get(
        re.compile(r".*/poolcops/42/alarms/history\?"),
        payload=[],
    )

    async with api:
        history = await api.get_alarm_history(
            42, start="2026-01-01T00:00:00Z", end="2026-01-31T23:59:59Z"
        )

    assert history == []


async def test_set_pump_on(api, mock_api):
    """Turn pump on."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/pump",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_pump(42, on=True)

    assert cmd.id == 1001


async def test_set_pump_off(api, mock_api):
    """Turn pump off."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/pump",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_pump(42, on=False)

    assert cmd.id == 1001


async def test_set_pump_speed(api, mock_api):
    """Set pump speed."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/pump/speed",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_pump_speed(42, "Speed3")

    assert cmd.id == 1001


async def test_set_pump_forced(api, mock_api):
    """Set forced pump mode."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/pump/forced",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_pump_forced(42, "Forced24H")

    assert cmd.id == 1001


async def test_set_valve_position(api, mock_api):
    """Set valve position."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/valve",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_valve_position(42, "Waste")

    assert cmd.id == 1001


async def test_set_auxiliary(api, mock_api):
    """Set auxiliary on."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/aux/AuxModule1/Aux1",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_auxiliary(42, "AuxModule1", "Aux1", on=True)

    assert cmd.id == 1001


async def test_get_auxiliaries(api, mock_api):
    """Get auxiliary configurations."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/state/aux",
        payload=[AUX_RESPONSE],
    )

    async with api:
        auxs = await api.get_auxiliaries(42)

    assert len(auxs) == 1
    assert auxs[0].friendly_name == "Pool Light"
    assert auxs[0].status is True


async def test_trigger_backwash(api, mock_api):
    """Trigger backwash."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/filter/backwash",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.trigger_backwash(42)

    assert cmd.id == 1001


async def test_trigger_ph_measure(api, mock_api):
    """Trigger pH measurement."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/pH/measure",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.trigger_ph_measure(42)

    assert cmd.id == 1001


async def test_trigger_orp_measure(api, mock_api):
    """Trigger ORP measurement."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/ORP/measure",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.trigger_orp_measure(42)

    assert cmd.id == 1001


async def test_set_water_valve_on(api, mock_api):
    """Open water level valve."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/waterlevel/valve",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_water_valve(42, on=True)

    assert cmd.id == 1001


async def test_set_water_valve_off(api, mock_api):
    """Close water level valve."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/waterlevel/valve",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_water_valve(42, on=False)

    assert cmd.id == 1001


async def test_get_commands(api, mock_api):
    """Get command history."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/commands",
        payload=[COMMAND_RESPONSE],
    )

    async with api:
        cmds = await api.get_commands(42)

    assert len(cmds) == 1
    assert cmds[0].label == "TestCommand"


async def test_get_pools(api, mock_api):
    """Get pools."""
    mock_api.get(f"{BASE_URL}/pools", payload=[POOL_RESPONSE])

    async with api:
        pools = await api.get_pools()

    assert len(pools) == 1
    assert pools[0].nickname == "Main Pool"


async def test_get_pool(api, mock_api):
    """Get a specific pool."""
    mock_api.get(f"{BASE_URL}/pools/10", payload=POOL_RESPONSE)

    async with api:
        pool = await api.get_pool(10)

    assert pool.id == 10
    assert pool.timezone == "Australia/Sydney"


async def test_get_profile(api, mock_api):
    """Get user profile."""
    mock_api.get(f"{BASE_URL}/profile", payload=PROFILE_RESPONSE)

    async with api:
        profile = await api.get_profile()

    assert profile.id == 5
    assert profile.email == "user@example.com"


# ------------------------------------------------------------------
# Edge cases: non-list responses from list endpoints
# ------------------------------------------------------------------


async def test_get_poolcops_non_list(api, mock_api):
    """Non-list response returns empty list."""
    mock_api.get(f"{BASE_URL}/poolcops", payload={"unexpected": True})

    async with api:
        result = await api.get_poolcops()

    assert result == []


async def test_get_alarms_non_list(api, mock_api):
    """Non-list alarm response returns empty list."""
    mock_api.get(f"{BASE_URL}/poolcops/42/alarms", payload={"unexpected": True})

    async with api:
        result = await api.get_alarms(42)

    assert result == []


async def test_get_alarm_history_non_list(api, mock_api):
    """Non-list alarm history response returns empty list."""
    mock_api.get(f"{BASE_URL}/poolcops/42/alarms/history", payload={"unexpected": True})

    async with api:
        result = await api.get_alarm_history(42)

    assert result == []


async def test_get_auxiliaries_non_list(api, mock_api):
    """Non-list auxiliaries response returns empty list."""
    mock_api.get(f"{BASE_URL}/poolcops/42/state/aux", payload={"unexpected": True})

    async with api:
        result = await api.get_auxiliaries(42)

    assert result == []


async def test_get_commands_non_list(api, mock_api):
    """Non-list commands response returns empty list."""
    mock_api.get(f"{BASE_URL}/poolcops/42/commands", payload={"unexpected": True})

    async with api:
        result = await api.get_commands(42)

    assert result == []


# ------------------------------------------------------------------
# Phase 2: Configuration endpoints
# ------------------------------------------------------------------


async def test_get_pump_config(api, mock_api):
    """Get pump configuration."""
    config = {"pumpType": "Variable", "speeds": 3}
    mock_api.get(f"{BASE_URL}/poolcops/42/configuration/pump", payload=config)

    async with api:
        result = await api.get_pump_config(42)

    assert result["pumpType"] == "Variable"


async def test_set_pump_config(api, mock_api):
    """Set pump configuration."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/configuration/pump",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_pump_config(42, {"pumpType": "Variable"})

    assert cmd.id == 1001


async def test_get_filter_config(api, mock_api):
    """Get filter configuration."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/configuration/filter",
        payload={"filterType": "Sand"},
    )

    async with api:
        result = await api.get_filter_config(42)

    assert result["filterType"] == "Sand"


async def test_set_filter_config(api, mock_api):
    """Set filter configuration."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/configuration/filter",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_filter_config(42, {"filterType": "Sand"})

    assert cmd.id == 1001


async def test_set_filtration_timers(api, mock_api):
    """Set filtration timers."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/configuration/filtrationtimers",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_filtration_timers(42, {"timers": []})

    assert cmd.id == 1001


async def test_set_forced_filtration(api, mock_api):
    """Set forced filtration mode."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/configuration/filtrationtimers/forced",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_forced_filtration(42, "Forced48H")

    assert cmd.id == 1001


async def test_get_pool_config(api, mock_api):
    """Get pool configuration."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/configuration/pool",
        payload={"poolType": "InGround"},
    )

    async with api:
        result = await api.get_pool_config(42)

    assert result["poolType"] == "InGround"


async def test_set_pool_config(api, mock_api):
    """Set pool configuration."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/configuration/pool",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_pool_config(42, {"poolType": "InGround"})

    assert cmd.id == 1001


async def test_get_ph_config(api, mock_api):
    """Get pH configuration."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/configuration/pH",
        payload={"setPoint": 7.2},
    )

    async with api:
        result = await api.get_ph_config(42)

    assert result["setPoint"] == 7.2


async def test_set_ph_config(api, mock_api):
    """Set pH configuration."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/configuration/pH",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_ph_config(42, {"setPoint": 7.4})

    assert cmd.id == 1001


async def test_get_orp_config(api, mock_api):
    """Get ORP configuration."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/configuration/orp",
        payload={"setPoint": 700},
    )

    async with api:
        result = await api.get_orp_config(42)

    assert result["setPoint"] == 700


async def test_set_orp_config(api, mock_api):
    """Set ORP configuration."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/configuration/orp",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_orp_config(42, {"setPoint": 750})

    assert cmd.id == 1001


async def test_get_waterlevel_config(api, mock_api):
    """Get water level configuration."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/configuration/waterlevel",
        payload={"mode": "Auto"},
    )

    async with api:
        result = await api.get_waterlevel_config(42)

    assert result["mode"] == "Auto"


async def test_set_waterlevel_config(api, mock_api):
    """Set water level configuration."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/configuration/waterlevel",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_waterlevel_config(42, {"mode": "Auto"})

    assert cmd.id == 1001


async def test_get_aux_configs(api, mock_api):
    """Get auxiliary configurations."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/configuration/aux",
        payload=[AUX_RESPONSE],
    )

    async with api:
        auxs = await api.get_aux_configs(42)

    assert len(auxs) == 1
    assert auxs[0].friendly_name == "Pool Light"


async def test_set_aux_config(api, mock_api):
    """Set auxiliary configuration."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/configuration/aux/AuxModule1/Aux1",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_aux_config(42, "AuxModule1", "Aux1", {"mode": "Timer"})

    assert cmd.id == 1001


async def test_get_equipments(api, mock_api):
    """Get equipment configuration."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/configuration/equipments",
        payload={"hasCover": True},
    )

    async with api:
        result = await api.get_equipments(42)

    assert result["hasCover"] is True


async def test_get_input_configs(api, mock_api):
    """Get input configurations."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/configuration/inputs",
        payload={"inputs": []},
    )

    async with api:
        result = await api.get_input_configs(42)

    assert result["inputs"] == []


async def test_get_versions(api, mock_api):
    """Get version information."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/configuration/versions",
        payload={"model": "Evolution"},
    )

    async with api:
        result = await api.get_versions(42)

    assert result["model"] == "Evolution"


async def test_get_network_config(api, mock_api):
    """Get network configuration."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/configuration/network",
        payload={"ipAddress": "192.168.1.100"},
    )

    async with api:
        result = await api.get_network_config(42)

    assert result["ipAddress"] == "192.168.1.100"


async def test_get_pools_non_list(api, mock_api):
    """Non-list pools response returns empty list."""
    mock_api.get(f"{BASE_URL}/pools", payload={"unexpected": True})

    async with api:
        result = await api.get_pools()

    assert result == []


async def test_get_aux_configs_non_list(api, mock_api):
    """Non-list aux configs response returns empty list."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/configuration/aux", payload={"unexpected": True}
    )

    async with api:
        result = await api.get_aux_configs(42)

    assert result == []


# ------------------------------------------------------------------
# Phase 3: Data & extras endpoints
# ------------------------------------------------------------------


async def test_get_datapoints(api, mock_api):
    """Get data points."""
    mock_api.get(
        re.compile(r".*/poolcops/42/bigpool/datapoints(\?|$)"),
        payload=[
            {"timestamp": "2026-01-15T12:00:00Z", "value": 7.2},
        ],
    )

    async with api:
        points = await api.get_datapoints(42, keys=["pH"])

    assert len(points) == 1
    assert points[0].value == 7.2


async def test_get_datapoints_dict_response(api, mock_api):
    """Get data points with dict wrapper response."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/bigpool/datapoints",
        payload={
            "dataPoints": [
                {"timestamp": "2026-01-15T12:00:00Z", "value": 7.2},
            ]
        },
    )

    async with api:
        points = await api.get_datapoints(42)

    assert len(points) == 1


async def test_get_datapoint(api, mock_api):
    """Get data points for a specific key."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/bigpool/datapoints/pH",
        payload=[
            {"timestamp": "2026-01-15T12:00:00Z", "value": 7.2},
        ],
    )

    async with api:
        points = await api.get_datapoint(42, "pH")

    assert len(points) == 1


async def test_get_datapoint_with_dates(api, mock_api):
    """Get data points with date range."""
    mock_api.get(
        re.compile(r".*/poolcops/42/bigpool/datapoints/pH\?"),
        payload=[],
    )

    async with api:
        points = await api.get_datapoint(42, "pH", start="2026-01-01", end="2026-01-31")

    assert points == []


async def test_get_datapoint_dict_response(api, mock_api):
    """Get data points for a key with dict wrapper."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/bigpool/datapoints/pH",
        payload={"items": [{"timestamp": "t1", "value": 7.0}]},
    )

    async with api:
        points = await api.get_datapoint(42, "pH")

    assert len(points) == 1


async def test_get_disconnections(api, mock_api):
    """Get disconnection times."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/bigpool/disconnections",
        payload=[
            {
                "start": "2026-01-15T10:00:00Z",
                "end": "2026-01-15T10:30:00Z",
                "duration": "00:30:00",
            }
        ],
    )

    async with api:
        disconnections = await api.get_disconnections(42)

    assert len(disconnections) == 1
    assert disconnections[0].duration == "00:30:00"


async def test_get_disconnections_dict_response(api, mock_api):
    """Get disconnections with dict wrapper."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/bigpool/disconnections",
        payload={
            "disconnections": [{"start": "t1", "end": "t2", "duration": "00:05:00"}]
        },
    )

    async with api:
        result = await api.get_disconnections(42)

    assert len(result) == 1


async def test_control_cover(api, mock_api):
    """Control pool cover."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/cover",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.control_cover(42, "Open")

    assert cmd.id == 1001


async def test_set_jetstream(api, mock_api):
    """Set jet stream on."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/jetstream",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_jetstream(42, on=True)

    assert cmd.id == 1001


async def test_set_suction_source(api, mock_api):
    """Set suction source."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/suction",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_suction_source(42, "Bottom")

    assert cmd.id == 1001


async def test_reboot(api, mock_api):
    """Reboot the unit."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/unit/reboot",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.reboot(42)

    assert cmd.id == 1001


async def test_set_screen_message(api, mock_api):
    """Set screen message."""
    mock_api.post(
        f"{BASE_URL}/poolcops/42/state/unit/screen",
        payload=COMMAND_RESPONSE,
    )

    async with api:
        cmd = await api.set_screen_message(42, "Hello!")

    assert cmd.id == 1001


async def test_clear_screen_message(api, mock_api):
    """Clear screen message."""
    mock_api.delete(
        f"{BASE_URL}/poolcops/42/state/unit/screen",
        status=200,
        content_type="application/json",
        payload={},
    )

    async with api:
        await api.clear_screen_message(42)


async def test_get_weather(api, mock_api):
    """Get current weather."""
    mock_api.get(
        f"{BASE_URL}/pools/10/weather/current",
        payload=WEATHER_RESPONSE,
    )

    async with api:
        weather = await api.get_weather(10)

    assert weather.temp_c == 28.5
    assert weather.condition_text == "Sunny"


async def test_get_weather_forecast(api, mock_api):
    """Get weather forecast."""
    forecast = {"forecast": {"forecastday": []}}
    mock_api.get(
        f"{BASE_URL}/pools/10/weather/forecast",
        payload=forecast,
    )

    async with api:
        result = await api.get_weather_forecast(10)

    assert "forecast" in result


async def test_get_datapoints_non_list_no_key(api, mock_api):
    """Non-list datapoints without known keys returns empty."""
    mock_api.get(f"{BASE_URL}/poolcops/42/bigpool/datapoints", payload={"other": True})

    async with api:
        result = await api.get_datapoints(42)

    assert result == []


async def test_get_datapoint_non_list_no_key(api, mock_api):
    """Non-list single datapoint without known keys returns empty."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/bigpool/datapoints/pH", payload={"other": True}
    )

    async with api:
        result = await api.get_datapoint(42, "pH")

    assert result == []


async def test_get_disconnections_non_list_no_key(api, mock_api):
    """Non-list disconnections without known keys returns empty."""
    mock_api.get(
        f"{BASE_URL}/poolcops/42/bigpool/disconnections", payload={"other": True}
    )

    async with api:
        result = await api.get_disconnections(42)

    assert result == []


async def test_get_datapoints_with_dates(api, mock_api):
    """Get data points with start/end date params."""
    mock_api.get(
        re.compile(r".*/poolcops/42/bigpool/datapoints\?"),
        payload=[{"timestamp": "2026-01-15T12:00:00Z", "value": 7.2}],
    )

    async with api:
        points = await api.get_datapoints(42, start="2026-01-01", end="2026-01-31")

    assert len(points) == 1
    assert points[0].value == 7.2
