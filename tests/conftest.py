"""Shared test fixtures for aiopoolcop tests."""

import pytest
from aioresponses import aioresponses

from aiopoolcop import PoolCopClientAPI

BASE_URL = "https://client-api.poolcop.net"

DEVICE_RESPONSE = {
    "id": 2478,
    "nickname": "Striker",
    "uuid": "09600011-2620-7caf-f22a-835fc72000f5",
    "mac": "02:09:60:00:11:26",
    "installationDate": "2022-07-05T00:00:04+02:00",
    "connectionDate": "2026-04-04T16:00:59+02:00",
    "lastPing": "00:00:10.5820637",
    "isFullyConnected": True,
    "cloudAccessState": "Unlimited",
    "state": {
        "pH": 7.5,
        "orp": 810,
        "airTemperature": 27,
        "waterTemperature": 27.2,
        "freeAvailableChlorine": 0,
        "totalChlorine": 0,
        "freeChlorine": 0,
        "batteryVoltage": 14.4,
        "mainsVoltage": 187,
        "salt": 0,
        "serviceMode": False,
        "pHDosing": False,
        "disinfectionDosing": False,
        "dateTime": "2026-04-04T16:00:55",
        "alarms": ["PressureLowPump1"],
        "pumpsInfo": [
            {
                "id": 0,
                "pumpCurrentSpeed": "Speed1",
                "pumpPressure": 76.5,
                "pumpState": True,
                "valvePosition": "Filter",
                "runningStatus": "TimerMode",
                "numberOfSpeeds": "Speed3",
                "filtrationMode": "Timer",
                "pumpForcedRemaining": "00:00:00",
            }
        ],
        "waterLevel": {
            "installed": True,
            "state": "Normal",
            "setPoint": "High",
            "isOnTarget": True,
            "isOnError": False,
            "isRefilling": False,
            "isMeasuring": False,
        },
        "jetStream": {"installed": False, "isRunning": False},
        "poolCover": {
            "installed": True,
            "controllable": False,
            "isClosing": False,
            "isOpening": False,
            "isOpen": False,
            "isStopped": True,
        },
        "flowVis": [],
        "inputs": {"Input1": True, "Input2": False},
        "auxiliaries": {"None": {"Aux1": True, "Aux2": False}},
    },
    "settings": {
        "pool": {
            "type": "RimflowTypeB",
            "volume": 77,
            "estimatedFlowrate": 9,
            "freezeProtection": False,
            "turnoverPerDay": 1,
        },
        "pH": {
            "installed": True,
            "setPoint": 7.5,
            "lowValue": 6.8,
            "highValue": 8.2,
            "autoAdjust": True,
            "mode": "phMinus",
            "maxDosingDuration": "00:10:00",
            "orpProtection": True,
        },
        "disinfection": {
            "lowShutdownTemperature": 7,
            "disinfectantType": "Chlorine",
            "mode": "ORP",
            "electrolyser": {
                "polarityInversionDuration": 4,
                "productionPercent": 80,
            },
            "orp": {
                "installed": True,
                "setPoint": 770,
                "lowValue": 500,
                "highValue": 900,
                "hyperchlorationSetPoint": 850,
                "hyperchlorationWeekday": "Monday",
            },
            "fac": {
                "installed": False,
                "setPoint": 0,
                "lowValue": 0,
                "highValue": 0,
                "protection": False,
            },
            "fc": {
                "installed": False,
                "setPoint": 0,
                "lowValue": 0,
                "highValue": 0,
            },
            "tc": {
                "installed": False,
                "lowValue": 0,
                "highValue": 0,
            },
        },
        "waterLevel": {
            "installed": True,
            "setPoint": "High",
            "canRefill": True,
            "canReduce": False,
            "maxFillDuration": "01:20:00",
            "drainingDuration": "00:10:00",
            "continuousFill": False,
            "reductionThreshold": 30,
        },
        "filtrations": [
            {
                "id": 1,
                "pumpType": "BaduEcoTouch",
                "filtrationMode": "Timer",
                "nbSpeeds": "Speed3",
                "speedCycle1": "Speed1",
                "speedCycle2": "Speed2",
                "speedCycle3": "Speed3",
                "speedCycle4": "Speed3",
                "speedBackwash": "Speed3",
                "speed24": "Speed1",
                "coverFiltrationSpeed": "Speed1",
                "coverFiltrationReduction": 5,
                "backwashFlowRate": 15.0,
                "flowRateMonitoringSpeed": "Speed1",
                "backwashTrigger": "Pressure",
                "filtrationValveType": "MultiPort",
                "rinseValveType": "None",
                "wasteLineValve": "None",
                "currentCycleElapsedTime": "01:30:00",
                "currentCycleRemainingTime": "02:30:00",
                "backwashPressure": 144,
                "backwashDuration": "00:02:30",
                "backwashTime": "11:00:00",
                "backwashMode": "Automatic",
                "maxIntervalBetweenBackwash": "14.00:00:00",
                "rinseDuration": "00:00:20",
                "alarmPressure": 51,
                "lowPressure": 52,
                "pumpProtection": True,
                "filterType": "Pressure",
                "timers": [
                    {"id": 1, "enabled": True, "timeOn": "23:59:00", "timeOff": "04:00:00"},
                    {"id": 2, "enabled": True, "timeOn": "08:00:00", "timeOff": "21:59:00"},
                ],
            }
        ],
        "auxs": {
            "None": {
                "Aux4": {
                    "id": "Aux4",
                    "auxChannel": 4,
                    "module": "None",
                    "moduleId": 0,
                    "label": "TransferPump",
                    "friendlyName": "Apf",
                    "status": False,
                    "isSlave": False,
                    "slavedTo": "NotSlave",
                    "mode": "Manual",
                    "isReserved": False,
                    "isHeatingControlled": False,
                    "heatingSetPoint": 0,
                    "pulseDuration": "00:00:00",
                    "moduleChannel": 0,
                    "daysOfWeek": [],
                    "timers": [{"id": 1, "timeOn": "00:00:00", "timeOff": "00:00:00"}],
                }
            }
        },
        "aco": {
            "installed": False,
            "flowRate": 0,
            "module": "None",
            "aux": "Aux1",
        },
        "remnant": {
            "installed": False,
            "flowRate": 0,
            "module": "None",
            "aux": "Aux1",
            "temperatureCompensation": False,
            "mode": "Manual",
        },
        "suctionValve": {
            "type": "None",
            "source": "None",
        },
    },
    "equipmentsInfo": {
        "hasPHSensor": True,
        "hasORPSensor": True,
        "hasAirTemperatureSensor": True,
        "hasFACSensor": False,
        "hasConductivitySensor": False,
        "hasSaltSensor": False,
        "hasWaterLevelSensor": True,
        "hasFCSensor": False,
        "hasTCSensor": False,
        "hasFlowMeter": False,
        "hasEnergyMeter": False,
        "hasPoolCover": True,
        "hasJetStream": False,
    },
    "history": {
        "pHLastInjectionDuration": None,
        "disinfectionLastInjectionDuration": None,
        "acoLastInjectionDuration": None,
        "remnantLastInjectionDuration": None,
        "lastpHMeasureDate": "2026-05-23T04:15:00",
        "lastRefillDate": "2026-05-16T22:28:00",
        "lastBackwashDate": "2026-05-16T11:03:00",
    },
    "versionInfo": {
        "poolCopVersion": "44.9.0",
        "model": "Evolution",
        "osVersion": "1.2.3",
    },
}

POOLS_RESPONSE = {
    "currentPage": 1,
    "pageSize": 100,
    "totalCount": 1,
    "totalPages": 1,
    "hasPreviousPage": False,
    "hasNextPage": False,
    "data": [
        {
            "id": 97138,
            "nickname": "Striker",
            "address1": "Test St 1",
            "zipCode": "1234 AB",
            "city": "TestCity",
            "country": "Netherlands",
            "latitude": 52.165958,
            "longitude": 6.038603,
            "timezone": "Europe/Amsterdam",
            "creationDate": "2022-07-06T08:22:37+02:00",
            "devices": [{"id": 2478, "nickname": "Striker"}],
        }
    ],
}

POOL_RESPONSE = POOLS_RESPONSE["data"][0]

COMMANDS_RESPONSE = {
    "currentPage": 1,
    "pageSize": 100,
    "totalCount": 2,
    "totalPages": 1,
    "hasPreviousPage": False,
    "hasNextPage": False,
    "data": [
        {
            "id": 7779477,
            "user": "Test User",
            "deviceId": 2478,
            "label": "SetTime",
            "isDelivered": True,
            "commandDate": "2026-03-31T17:04:26+02:00",
            "deliveryDate": "2026-03-31T17:04:29+02:00",
            "confirmationDate": "2026-03-31T17:04:30+02:00",
        }
    ],
}


@pytest.fixture
def api():
    """Create a PoolCopClientAPI client."""
    return PoolCopClientAPI(api_key="test-api-key")


@pytest.fixture
def mock_api():
    """Provide aioresponses mock."""
    with aioresponses() as m:
        yield m
