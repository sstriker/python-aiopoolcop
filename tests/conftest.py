"""Shared test fixtures for aiopoolcop tests."""

import pytest
from aioresponses import aioresponses

from aiopoolcop import PoolCopCloudAPI

BASE_URL = "https://cloud.api.poolcop.net/v1"

COMMAND_RESPONSE = {
    "id": 1001,
    "poolCopId": 42,
    "label": "TestCommand",
    "commandDate": "2026-01-15T10:00:00Z",
    "isDelivered": False,
}

STATE_RESPONSE = {
    "status": "Ready",
    "pumpsInfo": [
        {
            "id": 1,
            "pumpCurrentSpeed": "Speed2",
            "pumpForcedRemaining": "01:30:00",
            "pumpPressure": 1.2,
            "runningStatus": "Auto",
            "pumpState": True,
            "pumpPrimed": True,
            "valvePosition": "Filter",
        }
    ],
    "pH": 7.2,
    "orp": 650,
    "waterTemperature": 26.5,
    "dailyAverageWaterTemperature": 25.8,
    "airTemperature": 30.1,
    "batteryVoltage": 12.6,
    "mainsVoltage": 230.0,
    "mainsPowerLost": False,
    "freeAvailableChlorine": 1.5,
    "freeChlorine": 0.8,
    "totalChlorine": 1.2,
    "waterLevel": {
        "installed": True,
        "state": "Normal",
        "setPoint": "Normal",
        "isOnTarget": True,
        "isOnError": False,
    },
    "poolCover": {
        "installed": True,
        "controllable": True,
        "isClosing": False,
        "isOpening": False,
        "isStopped": True,
        "isOpen": False,
    },
    "jetStream": {
        "installed": True,
        "isRunning": False,
    },
    "flowVis": [
        {
            "installed": True,
            "pumpId": 1,
            "lowValue": 5.0,
            "highValue": 15.0,
            "flowRate": 10.5,
        }
    ],
    "auxiliaries": {
        "None": {"Aux1": True, "Aux2": False},
        "AuxModule1": {"Aux1": False, "Aux3": True},
    },
    "inputs": {
        "None": False,
        "Input1": True,
        "Input2": False,
    },
    "dateTime": "2026-01-15T12:00:00Z",
}

POOLCOP_RESPONSE = {
    "id": 42,
    "nickname": "My PoolCop",
    "uuid": "abc-123",
    "mac": "AA:BB:CC:DD:EE:FF",
    "poolId": 10,
    "userId": 5,
    "isConnected": True,
    "isFullyConnected": True,
    "connectionDate": "2025-06-01T08:00:00Z",
    "state": STATE_RESPONSE,
}

ALARM_RESPONSE = {
    "id": 1,
    "poolCopId": 42,
    "code": "A001",
    "severity": "Warning",
    "label": "Low pressure",
    "description": "Pump pressure is below threshold",
    "startDate": "2026-01-15T10:00:00Z",
    "endDate": None,
}

ALARM_HISTORY_RESPONSE = {
    "id": 2,
    "poolCopId": 42,
    "code": "A002",
    "severity": "Error",
    "label": "High temperature",
    "description": "Water temperature exceeded limit",
    "startDate": "2026-01-14T08:00:00Z",
    "endDate": "2026-01-14T12:00:00Z",
}

POOL_RESPONSE = {
    "id": 10,
    "nickname": "Main Pool",
    "latitude": -33.8688,
    "longitude": 151.2093,
    "timezone": "Australia/Sydney",
    "city": "Sydney",
    "country": "Australia",
}

PROFILE_RESPONSE = {
    "id": 5,
    "email": "user@example.com",
    "firstname": "Test",
    "lastname": "User",
    "timezone": "Australia/Sydney",
}

AUX_RESPONSE = {
    "auxChannel": 1,
    "moduleId": 0,
    "mode": "Auto",
    "label": "PoolLight",
    "friendlyName": "Pool Light",
    "isReserved": False,
    "status": True,
    "hasTimer": True,
    "isHeating": False,
    "heatingSetPoint": None,
}

WEATHER_RESPONSE = {
    "current": {
        "temp_c": 28.5,
        "humidity": 65,
        "condition": {"text": "Sunny"},
        "wind_kph": 12.3,
        "uv": 8.0,
    }
}


@pytest.fixture
def api():
    """Create a PoolCopCloudAPI client."""
    return PoolCopCloudAPI(token="test-token-123")


@pytest.fixture
def mock_api():
    """Provide aioresponses mock."""
    with aioresponses() as m:
        yield m
