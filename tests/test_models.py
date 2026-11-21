"""Tests for data models."""

from aiopoolcop.models import (
    AcoSettings,
    AuxSettings,
    AuxTimer,
    DeviceHistory,
    DeviceMinimalistic,
    DeviceSettings,
    DeviceState,
    DisinfectionSettings,
    ElectrolyserSettings,
    EquipmentsInfo,
    FacSettings,
    FcSettings,
    FiltrationSettings,
    FiltrationTimer,
    FlowVisInfo,
    JetStreamInfo,
    PhSettings,
    Pool,
    PoolCopCommand,
    PoolCopDevice,
    PoolCoverInfo,
    PoolSettings,
    PumpInfo,
    RemnantSettings,
    SuctionValveSettings,
    TcSettings,
    VersionInfo,
    WaterLevelInfo,
    WaterLevelSettings,
)

from .conftest import DEVICE_RESPONSE, POOL_RESPONSE


class TestPumpInfo:
    def test_from_dict(self):
        data = DEVICE_RESPONSE["state"]["pumpsInfo"][0]
        pump = PumpInfo.from_dict(data)
        assert pump.id == 0
        assert pump.current_speed == "Speed1"
        assert pump.running_status == "TimerMode"
        assert pump.filtration_mode == "Timer"
        assert pump.number_of_speeds == "Speed3"
        assert pump.pump_state is True
        assert pump.valve_position == "Filter"
        assert pump.pressure == 76.5
        assert pump.forced_remaining == "00:00:00"

    def test_defaults(self):
        pump = PumpInfo.from_dict({})
        assert pump.pump_state is False
        assert pump.running_status == "Stopped"
        assert pump.current_speed == "None"


class TestWaterLevelInfo:
    def test_from_dict(self):
        wl = WaterLevelInfo.from_dict(DEVICE_RESPONSE["state"]["waterLevel"])
        assert wl.installed is True
        assert wl.state == "Normal"
        assert wl.set_point == "High"
        assert wl.is_on_target is True
        assert wl.is_on_error is False
        assert wl.is_refilling is False
        assert wl.is_measuring is False

    def test_defaults(self):
        wl = WaterLevelInfo.from_dict({})
        assert wl.is_on_target is False
        assert wl.is_on_error is False


class TestPoolCoverInfo:
    def test_from_dict(self):
        pc = PoolCoverInfo.from_dict(DEVICE_RESPONSE["state"]["poolCover"])
        assert pc.installed is True
        assert pc.controllable is False
        assert pc.is_open is False
        assert pc.is_stopped is True


class TestJetStreamInfo:
    def test_from_dict(self):
        js = JetStreamInfo.from_dict({"installed": False, "isRunning": False})
        assert js.installed is False
        assert js.is_running is False


class TestFlowVisInfo:
    def test_from_dict(self):
        fv = FlowVisInfo.from_dict(
            {"installed": True, "pumpId": 1, "flowRate": 10.5, "type": "FV2"}
        )
        assert fv.installed is True
        assert fv.flow_rate == 10.5
        assert fv.type == "FV2"


class TestDeviceState:
    def test_from_dict_full(self):
        state = DeviceState.from_dict(DEVICE_RESPONSE["state"])
        assert state.ph == 7.5
        assert state.orp == 810
        assert state.water_temperature == 27.2
        assert state.air_temperature == 27
        assert state.battery_voltage == 14.4
        assert state.mains_voltage == 187
        assert state.salt == 0
        assert state.service_mode is False
        assert state.ph_dosing is False
        assert state.disinfection_dosing is False
        assert state.alarms == ["PressureLowPump1"]
        assert len(state.pumps) == 1
        assert state.water_level.installed is True
        assert state.inputs == {"Input1": True, "Input2": False}
        assert state.auxiliaries == {"None": {"Aux1": True, "Aux2": False}}

    def test_from_dict_minimal(self):
        state = DeviceState.from_dict({})
        assert state.ph == 0.0
        assert state.alarms == []
        assert state.pumps == []
        assert state.auxiliaries == {}


class TestFiltrationTimer:
    def test_from_dict(self):
        t = FiltrationTimer.from_dict(
            {"id": 1, "enabled": True, "timeOn": "08:00:00", "timeOff": "12:00:00"}
        )
        assert t.enabled is True
        assert t.time_on == "08:00:00"
        assert t.time_off == "12:00:00"


class TestFiltrationSettings:
    def test_from_dict(self):
        data = DEVICE_RESPONSE["settings"]["filtrations"][0]
        fs = FiltrationSettings.from_dict(data)
        assert fs.pump_type == "BaduEcoTouch"
        assert fs.filtration_mode == "Timer"
        assert fs.nb_speeds == "Speed3"
        assert fs.speed_cycle1 == "Speed1"
        assert fs.speed_cycle3 == "Speed3"
        assert fs.speed_cycle4 == "Speed3"
        assert fs.backwash_pressure == 144
        assert fs.backwash_flow_rate == 15.0
        assert fs.flow_rate_monitoring_speed == "Speed1"
        assert fs.backwash_trigger == "Pressure"
        assert fs.filtration_valve_type == "MultiPort"
        assert fs.rinse_valve_type == "None"
        assert fs.waste_line_valve == "None"
        assert fs.current_cycle_elapsed_time == "01:30:00"
        assert fs.current_cycle_remaining_time == "02:30:00"
        assert fs.pump_protection is True
        assert len(fs.timers) == 2
        assert fs.timers[0].enabled is True


class TestAuxSettings:
    def test_from_dict(self):
        data = DEVICE_RESPONSE["settings"]["auxs"]["None"]["Aux4"]
        aux = AuxSettings.from_dict(data)
        assert aux.id == "Aux4"
        assert aux.aux_channel == 4
        assert aux.label == "TransferPump"
        assert aux.friendly_name == "Apf"
        assert aux.is_reserved is False
        assert aux.is_heating_controlled is False
        assert aux.is_heating is False
        assert aux.heating_set_point == 0
        assert aux.pulse_duration == "00:00:00"
        assert aux.module_channel == 0
        assert aux.mode == "Manual"
        assert len(aux.timers) == 1

    def test_is_heating_fallback(self):
        aux = AuxSettings.from_dict(
            {"id": "Aux1", "isHeating": True, "auxChannel": 1, "module": "None"}
        )
        assert aux.is_heating_controlled is True
        assert aux.is_heating is True


class TestAuxTimer:
    def test_from_dict(self):
        t = AuxTimer.from_dict({"id": 1, "timeOn": "10:00:00", "timeOff": "12:00:00"})
        assert t.time_on == "10:00:00"


class TestPoolSettings:
    def test_from_dict(self):
        ps = PoolSettings.from_dict(DEVICE_RESPONSE["settings"]["pool"])
        assert ps.volume == 77
        assert ps.type == "RimflowTypeB"
        assert ps.freeze_protection is False
        assert ps.turnover_per_day == 1


class TestPhSettings:
    def test_from_dict(self):
        ph = PhSettings.from_dict(DEVICE_RESPONSE["settings"]["pH"])
        assert ph.installed is True
        assert ph.set_point == 7.5
        assert ph.mode == "phMinus"
        assert ph.auto_adjust is True
        assert ph.orp_protection is True


class TestDisinfectionSettings:
    def test_from_dict(self):
        dis = DisinfectionSettings.from_dict(
            DEVICE_RESPONSE["settings"]["disinfection"]
        )
        assert dis.disinfectant_type == "Chlorine"
        assert dis.mode == "ORP"
        assert dis.orp.set_point == 770
        assert dis.orp.installed is True
        assert dis.orp.low_value == 500
        assert dis.orp.high_value == 900
        assert dis.orp.hyperchlorination_set_point == 850
        assert dis.orp.hyperchlorination_weekday == "Monday"
        assert dis.electrolyser.polarity_inversion_duration == 4
        assert dis.electrolyser.production_percent == 80
        assert dis.fac.installed is False
        assert dis.fc.installed is False
        assert dis.tc.low_value == 0


class TestWaterLevelSettings:
    def test_from_dict(self):
        wl = WaterLevelSettings.from_dict(DEVICE_RESPONSE["settings"]["waterLevel"])
        assert wl.installed is True
        assert wl.set_point == "High"
        assert wl.can_refill is True
        assert wl.max_fill_duration == "01:20:00"
        assert wl.reduction_threshold == 30


class TestDeviceSettings:
    def test_from_dict(self):
        ds = DeviceSettings.from_dict(DEVICE_RESPONSE["settings"])
        assert ds.pool.volume == 77
        assert ds.ph.set_point == 7.5
        assert ds.disinfection.orp.set_point == 770
        assert ds.water_level.installed is True
        assert len(ds.filtrations) == 1
        assert len(ds.auxs) == 1
        assert ds.aco.installed is False
        assert ds.remnant.installed is False
        assert ds.remnant.mode == "Manual"
        assert ds.suction_valve.type == "None"

    def test_from_dict_empty(self):
        ds = DeviceSettings.from_dict({})
        assert ds.pool.volume == 0.0
        assert ds.filtrations == []
        assert ds.auxs == []
        assert ds.aco.installed is False
        assert ds.remnant.installed is False
        assert ds.suction_valve.type == "Standard"

    def test_auxs_list_format(self):
        ds = DeviceSettings.from_dict(
            {
                "auxs": [
                    {"id": "Aux1", "auxChannel": 1, "module": "None", "label": "Pump"},
                ],
            }
        )
        assert len(ds.auxs) == 1
        assert ds.auxs[0].id == "Aux1"


class TestEquipmentsInfo:
    def test_from_dict(self):
        eq = EquipmentsInfo.from_dict(DEVICE_RESPONSE["equipmentsInfo"])
        assert eq.has_ph_sensor is True
        assert eq.has_orp_sensor is True
        assert eq.has_jet_stream is False
        assert eq.has_flow_meter is False


class TestDeviceHistory:
    def test_from_dict(self):
        h = DeviceHistory.from_dict(DEVICE_RESPONSE["history"])
        assert h.last_backwash_date == "2026-05-16T11:03:00"
        assert h.last_refill_date == "2026-05-16T22:28:00"
        assert h.last_ph_measure_date == "2026-05-23T04:15:00"
        assert h.ph_last_injection_duration is None
        assert h.aco_last_injection_duration is None
        assert h.remnant_last_injection_duration is None


class TestVersionInfo:
    def test_from_dict(self):
        v = VersionInfo.from_dict(DEVICE_RESPONSE["versionInfo"])
        assert v.poolcop_version == "44.9.0"
        assert v.model == "Evolution"
        assert v.os_version == "1.2.3"


class TestPool:
    def test_from_dict(self):
        pool = Pool.from_dict(POOL_RESPONSE)
        assert pool.id == 97138
        assert pool.nickname == "Striker"
        assert pool.latitude == 52.165958
        assert pool.city == "TestCity"
        assert pool.timezone == "Europe/Amsterdam"
        assert len(pool.devices) == 1
        assert pool.devices[0].id == 2478

    def test_from_dict_minimal(self):
        pool = Pool.from_dict({"id": 1})
        assert pool.id == 1
        assert pool.nickname is None
        assert pool.devices == []


class TestDeviceMinimalistic:
    def test_from_dict(self):
        dm = DeviceMinimalistic.from_dict({"id": 2478, "nickname": "Striker"})
        assert dm.id == 2478
        assert dm.nickname == "Striker"


class TestPoolCopDevice:
    def test_from_dict(self):
        device = PoolCopDevice.from_dict(DEVICE_RESPONSE)
        assert device.id == 2478
        assert device.nickname == "Striker"
        assert device.is_fully_connected is True
        assert device.cloud_access_state == "Unlimited"
        assert device.version_info.model == "Evolution"
        assert device.state.ph == 7.5
        assert device.settings.pool.volume == 77

    def test_from_dict_minimal(self):
        device = PoolCopDevice.from_dict({"id": 1})
        assert device.id == 1
        assert device.state.ph == 0.0
        assert device.settings.pool.volume == 0.0


class TestElectrolyserSettings:
    def test_from_dict(self):
        es = ElectrolyserSettings.from_dict(
            {"polarityInversionDuration": 4, "productionPercent": 80}
        )
        assert es.polarity_inversion_duration == 4
        assert es.production_percent == 80

    def test_defaults(self):
        es = ElectrolyserSettings.from_dict({})
        assert es.polarity_inversion_duration == 0
        assert es.production_percent == 0


class TestFacSettings:
    def test_from_dict(self):
        fac = FacSettings.from_dict(
            {
                "installed": True,
                "setPoint": 1.5,
                "lowValue": 0.5,
                "highValue": 3.0,
                "protection": True,
            }
        )
        assert fac.installed is True
        assert fac.set_point == 1.5
        assert fac.protection is True


class TestFcSettings:
    def test_from_dict(self):
        fc = FcSettings.from_dict(
            {"installed": True, "setPoint": 1.0, "lowValue": 0.2, "highValue": 2.0}
        )
        assert fc.installed is True
        assert fc.set_point == 1.0


class TestTcSettings:
    def test_from_dict(self):
        tc = TcSettings.from_dict({"installed": True, "lowValue": 0, "highValue": 5})
        assert tc.installed is True
        assert tc.high_value == 5


class TestAcoSettings:
    def test_from_dict(self):
        aco = AcoSettings.from_dict(
            {"installed": True, "flowRate": 10, "module": "None", "aux": "Aux1"}
        )
        assert aco.installed is True
        assert aco.flow_rate == 10


class TestRemnantSettings:
    def test_from_dict(self):
        rem = RemnantSettings.from_dict(
            {
                "installed": True,
                "flowRate": 5,
                "module": "None",
                "aux": "Aux2",
                "temperatureCompensation": True,
                "mode": "Auto",
            }
        )
        assert rem.installed is True
        assert rem.temperature_compensation is True
        assert rem.mode == "Auto"


class TestSuctionValveSettings:
    def test_from_dict(self):
        sv = SuctionValveSettings.from_dict({"type": "ThreeWay", "source": "Skimmer"})
        assert sv.type == "ThreeWay"
        assert sv.source == "Skimmer"


class TestPoolCopCommand:
    def test_from_dict(self):
        cmd = PoolCopCommand.from_dict(
            {
                "id": 100,
                "deviceId": 2478,
                "user": "Test",
                "label": "SetTime",
                "isDelivered": True,
                "commandDate": "2026-01-01T00:00:00Z",
                "deliveryDate": "2026-01-01T00:00:01Z",
                "confirmationDate": "2026-01-01T00:00:02Z",
            }
        )
        assert cmd.id == 100
        assert cmd.device_id == 2478
        assert cmd.user == "Test"
        assert cmd.is_delivered is True
