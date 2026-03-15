"""Tests for data models."""

from aiopoolcop.models import (
    DataPoint,
    DisconnectionTime,
    FlowVisInfo,
    JetStreamInfo,
    Pool,
    PoolCopAlarm,
    PoolCopAuxiliary,
    PoolCopCommand,
    PoolCopDevice,
    PoolCopState,
    PoolCopSummary,
    PoolCoverInfo,
    PumpInfo,
    UserProfile,
    WaterLevelInfo,
    WeatherCondition,
    _parse_auxiliaries,
    _parse_inputs,
)


class TestPoolCopAlarm:
    def test_from_dict(self):
        data = {
            "id": 1,
            "poolCopId": 42,
            "code": "A001",
            "severity": "Warning",
            "label": "Low pressure",
            "description": "Pump pressure below threshold",
            "startDate": "2026-01-15T10:00:00Z",
            "endDate": None,
        }
        alarm = PoolCopAlarm.from_dict(data)
        assert alarm.id == 1
        assert alarm.pool_cop_id == 42
        assert alarm.code == "A001"
        assert alarm.severity == "Warning"
        assert alarm.label == "Low pressure"
        assert alarm.start_date == "2026-01-15T10:00:00Z"
        assert alarm.end_date is None

    def test_is_active_when_no_end_date(self):
        alarm = PoolCopAlarm(id=1, pool_cop_id=42)
        assert alarm.is_active is True

    def test_is_not_active_when_end_date(self):
        alarm = PoolCopAlarm(id=1, pool_cop_id=42, end_date="2026-01-15T12:00:00Z")
        assert alarm.is_active is False

    def test_from_dict_defaults(self):
        alarm = PoolCopAlarm.from_dict({})
        assert alarm.id == 0
        assert alarm.pool_cop_id == 0
        assert alarm.code is None
        assert alarm.severity == "Warning"
        assert alarm.label is None
        assert alarm.description is None
        assert alarm.start_date is None
        assert alarm.end_date is None


class TestPumpInfo:
    def test_from_dict(self):
        data = {
            "id": 1,
            "pumpCurrentSpeed": "Speed3",
            "pumpForcedRemaining": "02:00:00",
            "pumpPressure": 1.5,
            "runningStatus": "Forced",
            "pumpState": True,
            "pumpPrimed": True,
            "valvePosition": "Waste",
        }
        pump = PumpInfo.from_dict(data)
        assert pump.id == 1
        assert pump.current_speed == "Speed3"
        assert pump.forced_remaining == "02:00:00"
        assert pump.pressure == 1.5
        assert pump.running_status == "Forced"
        assert pump.pump_state is True
        assert pump.pump_primed is True
        assert pump.valve_position == "Waste"

    def test_from_dict_defaults(self):
        pump = PumpInfo.from_dict({})
        assert pump.id == 0
        assert pump.current_speed == "None"
        assert pump.forced_remaining == "00:00:00"
        assert pump.running_status == "Stop"
        assert pump.pump_state is False
        assert pump.pump_primed is False
        assert pump.valve_position == "Filter"
        assert pump.pressure == 0.0


class TestWaterLevelInfo:
    def test_from_dict(self):
        data = {
            "installed": True,
            "state": "Low",
            "setPoint": "High",
            "isOnTarget": False,
            "isOnError": True,
        }
        wl = WaterLevelInfo.from_dict(data)
        assert wl.installed is True
        assert wl.state == "Low"
        assert wl.set_point == "High"
        assert wl.is_on_target is False
        assert wl.is_on_error is True

    def test_from_dict_defaults(self):
        wl = WaterLevelInfo.from_dict({})
        assert wl.installed is False
        assert wl.state == "Normal"
        assert wl.set_point == "Unknown"
        assert wl.is_on_target is None
        assert wl.is_on_error is None


class TestPoolCoverInfo:
    def test_from_dict(self):
        data = {
            "installed": True,
            "controllable": True,
            "isClosing": True,
            "isOpening": False,
            "isStopped": False,
            "isOpen": False,
        }
        cover = PoolCoverInfo.from_dict(data)
        assert cover.installed is True
        assert cover.controllable is True
        assert cover.is_closing is True
        assert cover.is_opening is False
        assert cover.is_stopped is False
        assert cover.is_open is False

    def test_from_dict_defaults(self):
        cover = PoolCoverInfo.from_dict({})
        assert cover.installed is False
        assert cover.controllable is False
        assert cover.is_stopped is True


class TestJetStreamInfo:
    def test_from_dict(self):
        info = JetStreamInfo.from_dict({"installed": True, "isRunning": True})
        assert info.installed is True
        assert info.is_running is True

    def test_from_dict_defaults(self):
        info = JetStreamInfo.from_dict({})
        assert info.installed is False
        assert info.is_running is False


class TestFlowVisInfo:
    def test_from_dict(self):
        data = {
            "installed": True,
            "pumpId": 1,
            "lowValue": 5.0,
            "highValue": 15.0,
            "flowRate": 10.5,
        }
        fv = FlowVisInfo.from_dict(data)
        assert fv.installed is True
        assert fv.pump_id == 1
        assert fv.low_value == 5.0
        assert fv.high_value == 15.0
        assert fv.flow_rate == 10.5

    def test_from_dict_defaults(self):
        fv = FlowVisInfo.from_dict({})
        assert fv.installed is False
        assert fv.flow_rate == 0.0


class TestParseAuxiliaries:
    def test_parse_merged_auxiliaries(self):
        data = {
            "auxiliaries": {
                "None": {"None": False, "Aux1": True},
                "AuxModule1": {"None": False, "Aux1": False, "Aux2": True},
            }
        }
        result = _parse_auxiliaries(data)
        assert "AuxModule1" in result
        assert result["AuxModule1"]["Aux2"] is True
        assert "None" not in result

    def test_parse_uf_legacy_fallback(self):
        data = {
            "auxiliaries": None,
            "auxiliariesUFLegacy": {
                "None": {"Aux1": True},
                "AuxModule1": {"Aux1": False},
            },
        }
        result = _parse_auxiliaries(data)
        assert "AuxModule1" in result

    def test_parse_satellite_fallback(self):
        data = {
            "auxiliaries": None,
            "auxiliariesSatellite": {
                "None": {"Aux1": True},
                "AuxModule2": {"Aux1": True},
            },
        }
        result = _parse_auxiliaries(data)
        assert "AuxModule2" in result

    def test_parse_empty(self):
        result = _parse_auxiliaries({})
        assert result == {}


class TestParseInputs:
    def test_parse_merged_inputs(self):
        data = {"inputs": {"None": False, "Input1": True, "Input2": False}}
        result = _parse_inputs(data)
        assert result == {"Input1": True, "Input2": False}

    def test_parse_uf_legacy_fallback(self):
        data = {
            "inputs": None,
            "inputsUFLegacy": {"None": False, "Input1": True},
        }
        result = _parse_inputs(data)
        assert result == {"Input1": True}

    def test_parse_satellite_fallback(self):
        data = {
            "inputs": None,
            "inputsSatellite": {"None": False, "Input1": True},
        }
        result = _parse_inputs(data)
        assert result == {"Input1": True}

    def test_parse_empty(self):
        result = _parse_inputs({})
        assert result == {}


class TestPoolCopState:
    def test_from_dict_full(self):
        data = {
            "status": "Ready",
            "pumpsInfo": [
                {
                    "id": 1,
                    "pumpCurrentSpeed": "Speed2",
                    "runningStatus": "Auto",
                    "pumpState": True,
                    "pumpPrimed": True,
                    "valvePosition": "Filter",
                    "pumpPressure": 1.2,
                }
            ],
            "pH": 7.2,
            "orp": 650,
            "waterTemperature": 26.5,
            "dailyAverageWaterTemperature": 25.0,
            "airTemperature": 30.0,
            "batteryVoltage": 12.6,
            "mainsVoltage": 230.0,
            "mainsPowerLost": False,
            "freeAvailableChlorine": 1.5,
            "freeChlorine": 0.8,
            "totalChlorine": 1.2,
            "waterLevel": {"installed": True, "state": "Normal"},
            "poolCover": {"installed": True, "controllable": True},
            "jetStream": {"installed": False},
            "flowVis": [{"installed": True, "pumpId": 1, "flowRate": 10.0}],
            "auxiliaries": {"AuxModule1": {"Aux1": True}},
            "inputs": {"Input1": True},
            "dateTime": "2026-01-15T12:00:00Z",
        }
        state = PoolCopState.from_dict(data)
        assert state.status == "Ready"
        assert len(state.pumps) == 1
        assert state.pumps[0].current_speed == "Speed2"
        assert state.ph == 7.2
        assert state.orp == 650
        assert state.water_temperature == 26.5
        assert state.water_level.installed is True
        assert state.pool_cover.installed is True
        assert state.jet_stream.installed is False
        assert len(state.flow_vis) == 1
        assert state.flow_vis[0].flow_rate == 10.0
        assert state.auxiliaries["AuxModule1"]["Aux1"] is True
        assert state.inputs["Input1"] is True
        assert state.date_time == "2026-01-15T12:00:00Z"

    def test_from_dict_minimal(self):
        state = PoolCopState.from_dict({})
        assert state.status == "Ready"
        assert state.pumps == []
        assert state.ph == 0.0
        assert state.orp == 0
        assert state.water_level.installed is False
        assert state.auxiliaries == {}
        assert state.inputs == {}

    def test_from_dict_none_sub_objects(self):
        data = {
            "pumpsInfo": None,
            "waterLevel": None,
            "poolCover": None,
            "jetStream": None,
            "flowVis": None,
        }
        state = PoolCopState.from_dict(data)
        assert state.pumps == []
        assert state.water_level.installed is False
        assert state.flow_vis == []


class TestPoolCopSummary:
    def test_from_dict(self):
        data = {
            "id": 42,
            "nickname": "My PoolCop",
            "uuid": "abc-123",
            "mac": "AA:BB:CC:DD:EE:FF",
            "poolId": 10,
            "userId": 5,
            "isConnected": True,
            "isFullyConnected": True,
            "connectionDate": "2025-06-01T08:00:00Z",
        }
        summary = PoolCopSummary.from_dict(data)
        assert summary.id == 42
        assert summary.nickname == "My PoolCop"
        assert summary.uuid == "abc-123"
        assert summary.mac == "AA:BB:CC:DD:EE:FF"
        assert summary.pool_id == 10
        assert summary.is_connected is True

    def test_from_dict_defaults(self):
        summary = PoolCopSummary.from_dict({})
        assert summary.id == 0
        assert summary.nickname is None
        assert summary.is_connected is False


class TestPoolCopDevice:
    def test_from_dict(self):
        data = {
            "id": 42,
            "nickname": "My PoolCop",
            "isConnected": True,
            "state": {
                "pH": 7.4,
                "orp": 700,
                "waterTemperature": 28.0,
            },
        }
        device = PoolCopDevice.from_dict(data)
        assert device.id == 42
        assert device.nickname == "My PoolCop"
        assert device.is_connected is True
        assert device.state.ph == 7.4
        assert device.state.orp == 700

    def test_from_dict_no_state(self):
        device = PoolCopDevice.from_dict({"id": 1})
        assert device.state.status == "Ready"


class TestPool:
    def test_from_dict(self):
        data = {
            "id": 10,
            "nickname": "Main Pool",
            "latitude": -33.8688,
            "longitude": 151.2093,
            "timezone": "Australia/Sydney",
            "city": "Sydney",
            "country": "Australia",
        }
        pool = Pool.from_dict(data)
        assert pool.id == 10
        assert pool.nickname == "Main Pool"
        assert pool.latitude == -33.8688
        assert pool.timezone == "Australia/Sydney"

    def test_from_dict_defaults(self):
        pool = Pool.from_dict({})
        assert pool.id == 0
        assert pool.nickname is None
        assert pool.latitude is None


class TestUserProfile:
    def test_from_dict(self):
        data = {
            "id": 5,
            "email": "user@example.com",
            "firstname": "Test",
            "lastname": "User",
            "timezone": "Australia/Sydney",
        }
        profile = UserProfile.from_dict(data)
        assert profile.id == 5
        assert profile.email == "user@example.com"
        assert profile.firstname == "Test"

    def test_from_dict_defaults(self):
        profile = UserProfile.from_dict({})
        assert profile.id == 0
        assert profile.email is None


class TestPoolCopCommand:
    def test_from_dict(self):
        data = {
            "id": 1001,
            "poolCopId": 42,
            "label": "SetPump",
            "commandDate": "2026-01-15T10:00:00Z",
            "deliveryDate": "2026-01-15T10:00:05Z",
            "confirmationDate": "2026-01-15T10:00:10Z",
            "isDelivered": True,
            "returnCode": 0,
        }
        cmd = PoolCopCommand.from_dict(data)
        assert cmd.id == 1001
        assert cmd.pool_cop_id == 42
        assert cmd.label == "SetPump"
        assert cmd.is_delivered is True
        assert cmd.return_code == 0

    def test_from_dict_defaults(self):
        cmd = PoolCopCommand.from_dict({})
        assert cmd.id == 0
        assert cmd.is_delivered is False
        assert cmd.return_code is None


class TestPoolCopAuxiliary:
    def test_from_dict(self):
        data = {
            "auxChannel": 1,
            "moduleId": 0,
            "mode": "Auto",
            "label": "PoolLight",
            "friendlyName": "Pool Light",
            "isReserved": False,
            "status": True,
            "hasTimer": True,
            "isHeating": False,
            "heatingSetPoint": 28.0,
        }
        aux = PoolCopAuxiliary.from_dict(data)
        assert aux.aux_channel == 1
        assert aux.mode == "Auto"
        assert aux.label == "PoolLight"
        assert aux.friendly_name == "Pool Light"
        assert aux.status is True
        assert aux.heating_set_point == 28.0

    def test_from_dict_defaults(self):
        aux = PoolCopAuxiliary.from_dict({})
        assert aux.aux_channel == 0
        assert aux.mode is None
        assert aux.status is False


class TestDataPoint:
    def test_from_dict(self):
        data = {"timestamp": "2026-01-15T12:00:00Z", "value": 7.2}
        dp = DataPoint.from_dict(data)
        assert dp.timestamp == "2026-01-15T12:00:00Z"
        assert dp.value == 7.2

    def test_from_dict_defaults(self):
        dp = DataPoint.from_dict({})
        assert dp.timestamp == ""
        assert dp.value is None


class TestDisconnectionTime:
    def test_from_dict(self):
        data = {
            "start": "2026-01-15T10:00:00Z",
            "end": "2026-01-15T10:30:00Z",
            "duration": "00:30:00",
        }
        dt = DisconnectionTime.from_dict(data)
        assert dt.start == "2026-01-15T10:00:00Z"
        assert dt.end == "2026-01-15T10:30:00Z"
        assert dt.duration == "00:30:00"

    def test_from_dict_defaults(self):
        dt = DisconnectionTime.from_dict({})
        assert dt.start == ""
        assert dt.end == ""
        assert dt.duration == ""


class TestWeatherCondition:
    def test_from_dict_with_current(self):
        data = {
            "current": {
                "temp_c": 28.5,
                "humidity": 65,
                "condition": {"text": "Sunny"},
                "wind_kph": 12.3,
                "uv": 8.0,
            }
        }
        w = WeatherCondition.from_dict(data)
        assert w.temp_c == 28.5
        assert w.humidity == 65
        assert w.condition_text == "Sunny"
        assert w.wind_kph == 12.3
        assert w.uv == 8.0

    def test_from_dict_flat(self):
        data = {
            "temp_c": 25.0,
            "humidity": 70,
            "condition": {"text": "Cloudy"},
            "wind_kph": 5.0,
            "uv": 3.0,
        }
        w = WeatherCondition.from_dict(data)
        assert w.temp_c == 25.0

    def test_from_dict_defaults(self):
        w = WeatherCondition.from_dict({})
        assert w.temp_c == 0.0
        assert w.humidity == 0
        assert w.condition_text == ""
