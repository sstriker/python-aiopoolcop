"""Data models for PoolCop Client API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# State sub-models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PumpInfo:
    """Represents pump state information."""

    id: int = 0
    current_speed: str = "None"
    forced_remaining: str = "00:00:00"
    running_status: str = "Stopped"
    filtration_mode: str = "Timer"
    number_of_speeds: str = "Speed1"
    pump_state: bool = False
    valve_position: str = "Filter"
    pressure: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PumpInfo:
        """Create a PumpInfo from an API response dict."""
        return cls(
            id=data.get("id", 0),
            current_speed=data.get("pumpCurrentSpeed", "None"),
            forced_remaining=data.get("pumpForcedRemaining", "00:00:00"),
            running_status=data.get("runningStatus", "Stopped"),
            filtration_mode=data.get("filtrationMode", "Timer"),
            number_of_speeds=data.get("numberOfSpeeds", "Speed1"),
            pump_state=data.get("pumpState", False),
            valve_position=data.get("valvePosition", "Filter"),
            pressure=data.get("pumpPressure", 0.0),
        )


@dataclass(frozen=True)
class WaterLevelInfo:
    """Represents water level state information."""

    installed: bool = False
    state: str = "Normal"
    set_point: str = "Unknown"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WaterLevelInfo:
        """Create a WaterLevelInfo from an API response dict."""
        return cls(
            installed=data.get("installed", False),
            state=data.get("state", "Normal"),
            set_point=data.get("setPoint", "Unknown"),
        )


@dataclass(frozen=True)
class PoolCoverInfo:
    """Represents pool cover state information."""

    installed: bool = False
    controllable: bool = False
    is_closing: bool = False
    is_opening: bool = False
    is_stopped: bool = True
    is_open: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolCoverInfo:
        """Create a PoolCoverInfo from an API response dict."""
        return cls(
            installed=data.get("installed", False),
            controllable=data.get("controllable", False),
            is_closing=data.get("isClosing", False),
            is_opening=data.get("isOpening", False),
            is_stopped=data.get("isStopped", True),
            is_open=data.get("isOpen", False),
        )


@dataclass(frozen=True)
class JetStreamInfo:
    """Represents jet stream state information."""

    installed: bool = False
    is_running: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> JetStreamInfo:
        """Create a JetStreamInfo from an API response dict."""
        return cls(
            installed=data.get("installed", False),
            is_running=data.get("isRunning", False),
        )


@dataclass(frozen=True)
class FlowVisInfo:
    """Represents flow meter state information."""

    installed: bool = False
    pump_id: int = 0
    flow_rate: float = 0.0
    type: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FlowVisInfo:
        """Create a FlowVisInfo from an API response dict."""
        return cls(
            installed=data.get("installed", False),
            pump_id=data.get("pumpId", 0),
            flow_rate=data.get("flowRate", 0.0),
            type=data.get("type", ""),
        )


@dataclass(frozen=True)
class DeviceState:
    """Represents the full state of a PoolCop device."""

    ph: float = 0.0
    orp: int = 0
    water_temperature: float = 0.0
    air_temperature: float = 0.0
    battery_voltage: float = 0.0
    mains_voltage: float = 0.0
    salt: float = 0.0
    free_available_chlorine: float = 0.0
    free_chlorine: float = 0.0
    total_chlorine: float = 0.0
    service_mode: bool = False
    ph_dosing: bool = False
    disinfection_dosing: bool = False
    date_time: str = ""
    alarms: list[str] = field(default_factory=list)
    pumps: list[PumpInfo] = field(default_factory=list)
    water_level: WaterLevelInfo = field(default_factory=WaterLevelInfo)
    pool_cover: PoolCoverInfo = field(default_factory=PoolCoverInfo)
    jet_stream: JetStreamInfo = field(default_factory=JetStreamInfo)
    flow_vis: list[FlowVisInfo] = field(default_factory=list)
    auxiliaries: dict[str, dict[str, bool]] = field(default_factory=dict)
    inputs: dict[str, bool] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceState:
        """Create a DeviceState from an API response dict."""
        pumps_data = data.get("pumpsInfo") or []
        wl_data = data.get("waterLevel") or {}
        pc_data = data.get("poolCover") or {}
        js_data = data.get("jetStream") or {}
        fv_data = data.get("flowVis") or []

        # Alarms are string codes in the client API
        alarms_raw = data.get("alarms") or []
        alarms = [str(a) for a in alarms_raw] if isinstance(alarms_raw, list) else []

        # Auxiliaries: nested dict {module: {aux: bool}}
        aux_raw = data.get("auxiliaries") or {}
        auxiliaries = {}
        if isinstance(aux_raw, dict):
            for module, ports in aux_raw.items():
                if isinstance(ports, dict):
                    auxiliaries[module] = {k: v for k, v in ports.items()}

        # Inputs: {name: bool}
        inputs_raw = data.get("inputs") or {}
        inputs = (
            {k: v for k, v in inputs_raw.items()}
            if isinstance(inputs_raw, dict)
            else {}
        )

        return cls(
            ph=data.get("pH", 0.0),
            orp=data.get("orp", 0),
            water_temperature=data.get("waterTemperature", 0.0),
            air_temperature=data.get("airTemperature", 0.0),
            battery_voltage=data.get("batteryVoltage", 0.0),
            mains_voltage=data.get("mainsVoltage", 0.0),
            salt=data.get("salt", 0.0),
            free_available_chlorine=data.get("freeAvailableChlorine", 0.0),
            free_chlorine=data.get("freeChlorine", 0.0),
            total_chlorine=data.get("totalChlorine", 0.0),
            service_mode=data.get("serviceMode", False),
            ph_dosing=data.get("pHDosing", False),
            disinfection_dosing=data.get("disinfectionDosing", False),
            date_time=data.get("dateTime", ""),
            alarms=alarms,
            pumps=[PumpInfo.from_dict(p) for p in pumps_data],
            water_level=WaterLevelInfo.from_dict(wl_data),
            pool_cover=PoolCoverInfo.from_dict(pc_data),
            jet_stream=JetStreamInfo.from_dict(js_data),
            flow_vis=[FlowVisInfo.from_dict(f) for f in fv_data],
            auxiliaries=auxiliaries,
            inputs=inputs,
        )


# Backwards-compatible alias
PoolCopState = DeviceState


# ---------------------------------------------------------------------------
# Settings sub-models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FiltrationTimer:
    """A filtration cycle timer."""

    id: int = 0
    enabled: bool = False
    time_on: str = "00:00:00"
    time_off: str = "00:00:00"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FiltrationTimer:
        return cls(
            id=data.get("id", 0),
            enabled=data.get("enabled", False),
            time_on=data.get("timeOn", "00:00:00"),
            time_off=data.get("timeOff", "00:00:00"),
        )


@dataclass(frozen=True)
class FiltrationSettings:
    """Filtration group settings."""

    id: int = 0
    pump_type: str = "Unknown"
    filtration_mode: str = "Timer"
    nb_speeds: str = "Speed1"
    speed_cycle1: str = "Speed1"
    speed_cycle2: str = "Speed1"
    speed_backwash: str = "Speed1"
    speed_24: str = "Speed1"
    cover_filtration_speed: str = "Speed1"
    cover_filtration_reduction: int = 0
    backwash_pressure: float = 0.0
    backwash_duration: str = "00:00:00"
    backwash_time: str = "00:00:00"
    backwash_mode: str = "Automatic"
    max_interval_between_backwash: str = ""
    rinse_duration: str = "00:00:00"
    alarm_pressure: float = 0.0
    low_pressure: float = 0.0
    pump_protection: bool = False
    filter_type: str = "Pressure"
    timers: list[FiltrationTimer] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FiltrationSettings:
        timers_raw = data.get("timers") or []
        return cls(
            id=data.get("id", 0),
            pump_type=str(data.get("pumpType", "Unknown")),
            filtration_mode=str(data.get("filtrationMode", "Timer")),
            nb_speeds=str(data.get("nbSpeeds", "Speed1")),
            speed_cycle1=str(data.get("speedCycle1", "Speed1")),
            speed_cycle2=str(data.get("speedCycle2", "Speed1")),
            speed_backwash=str(data.get("speedBackwash", "Speed1")),
            speed_24=str(data.get("speed24", "Speed1")),
            cover_filtration_speed=str(data.get("coverFiltrationSpeed", "Speed1")),
            cover_filtration_reduction=data.get("coverFiltrationReduction", 0),
            backwash_pressure=data.get("backwashPressure", 0.0),
            backwash_duration=data.get("backwashDuration", "00:00:00"),
            backwash_time=data.get("backwashTime", "00:00:00"),
            backwash_mode=data.get("backwashMode", "Automatic"),
            max_interval_between_backwash=data.get(
                "maxIntervalBetweenBackwash", ""
            ),
            rinse_duration=data.get("rinseDuration", "00:00:00"),
            alarm_pressure=data.get("alarmPressure", 0.0),
            low_pressure=data.get("lowPressure", 0.0),
            pump_protection=data.get("pumpProtection", False),
            filter_type=data.get("filterType", "Pressure"),
            timers=[FiltrationTimer.from_dict(t) for t in timers_raw],
        )


@dataclass(frozen=True)
class AuxTimer:
    """An auxiliary timer."""

    id: int = 0
    time_on: str = "00:00:00"
    time_off: str = "00:00:00"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuxTimer:
        return cls(
            id=data.get("id", 0),
            time_on=data.get("timeOn", "00:00:00"),
            time_off=data.get("timeOff", "00:00:00"),
        )


@dataclass(frozen=True)
class AuxSettings:
    """Auxiliary port configuration from settings."""

    id: str = ""
    aux_channel: int = 0
    module: str = "None"
    module_id: int = 0
    label: str = ""
    friendly_name: str = ""
    status: bool = False
    is_slave: bool = False
    slaved_to: str = "NotSlave"
    mode: str = "Off"
    is_reserved: bool = False
    is_heating: bool = False
    days_of_week: list[str] = field(default_factory=list)
    timers: list[AuxTimer] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuxSettings:
        timers_raw = data.get("timers") or []
        days_raw = data.get("daysOfWeek") or []
        return cls(
            id=data.get("id", ""),
            aux_channel=data.get("auxChannel", 0),
            module=data.get("module", "None"),
            module_id=data.get("moduleId", 0),
            label=data.get("label", ""),
            friendly_name=data.get("friendlyName", ""),
            status=data.get("status", False),
            is_slave=data.get("isSlave", False),
            slaved_to=data.get("slavedTo", "NotSlave"),
            mode=data.get("mode", "Off"),
            is_reserved=data.get("isReserved", False),
            is_heating=data.get("isHeating", False),
            days_of_week=list(days_raw),
            timers=[AuxTimer.from_dict(t) for t in timers_raw],
        )


# Backwards-compatible alias
PoolCopAuxiliary = AuxSettings


@dataclass(frozen=True)
class PoolSettings:
    """Pool configuration."""

    type: str = "ClassicPool"
    volume: float = 0.0
    estimated_flowrate: float = 0.0
    freeze_protection: bool = False
    turnover_per_day: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolSettings:
        return cls(
            type=data.get("type", "ClassicPool"),
            volume=data.get("volume", 0.0),
            estimated_flowrate=data.get("estimatedFlowrate", 0.0),
            freeze_protection=data.get("freezeProtection", False),
            turnover_per_day=data.get("turnoverPerDay", 0.0),
        )


@dataclass(frozen=True)
class PhSettings:
    """pH control settings."""

    installed: bool = False
    set_point: float = 7.2
    low_value: float = 6.8
    high_value: float = 8.2
    auto_adjust: bool = False
    mode: str = "ReadOnly"
    max_dosing_duration: str = "00:00:00"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PhSettings:
        return cls(
            installed=data.get("installed", False),
            set_point=data.get("setPoint", 7.2),
            low_value=data.get("lowValue", 6.8),
            high_value=data.get("highValue", 8.2),
            auto_adjust=data.get("autoAdjust", False),
            mode=data.get("mode", "ReadOnly"),
            max_dosing_duration=data.get("maxDosingDuration", "00:00:00"),
        )


@dataclass(frozen=True)
class OrpSettings:
    """ORP/disinfection control settings."""

    installed: bool = False
    set_point: int = 650

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OrpSettings:
        return cls(
            installed=data.get("installed", False),
            set_point=data.get("setPoint", 650),
        )


@dataclass(frozen=True)
class DisinfectionSettings:
    """Disinfection settings."""

    low_shutdown_temperature: float = 0.0
    disinfectant_type: str = "ReadOnly"
    orp: OrpSettings = field(default_factory=OrpSettings)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DisinfectionSettings:
        orp_data = data.get("orp") or {}
        return cls(
            low_shutdown_temperature=data.get("lowShutdownTemperature", 0.0),
            disinfectant_type=data.get("disinfectantType", "ReadOnly"),
            orp=OrpSettings.from_dict(orp_data),
        )


@dataclass(frozen=True)
class WaterLevelSettings:
    """Water level settings."""

    installed: bool = False
    set_point: str = "Normal"
    can_refill: bool = False
    can_reduce: bool = False
    max_fill_duration: str = "00:00:00"
    draining_duration: str = "00:00:00"
    continuous_fill: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WaterLevelSettings:
        return cls(
            installed=data.get("installed", False),
            set_point=data.get("setPoint", "Normal"),
            can_refill=data.get("canRefill", False),
            can_reduce=data.get("canReduce", False),
            max_fill_duration=data.get("maxFillDuration", "00:00:00"),
            draining_duration=data.get("drainingDuration", "00:00:00"),
            continuous_fill=data.get("continuousFill", False),
        )


@dataclass(frozen=True)
class DeviceSettings:
    """All device settings."""

    pool: PoolSettings = field(default_factory=PoolSettings)
    ph: PhSettings = field(default_factory=PhSettings)
    disinfection: DisinfectionSettings = field(default_factory=DisinfectionSettings)
    water_level: WaterLevelSettings = field(default_factory=WaterLevelSettings)
    filtrations: list[FiltrationSettings] = field(default_factory=list)
    auxs: list[AuxSettings] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceSettings:
        pool_data = data.get("pool") or {}
        ph_data = data.get("pH") or {}
        dis_data = data.get("disinfection") or {}
        wl_data = data.get("waterLevel") or {}
        filt_data = data.get("filtrations") or []
        # auxs can be nested dict {module: {aux: {...}}} or list
        auxs_raw = data.get("auxs") or {}
        auxs = []
        if isinstance(auxs_raw, dict):
            for _module, ports in auxs_raw.items():
                if isinstance(ports, dict):
                    for _aux_id, aux_data in ports.items():
                        if isinstance(aux_data, dict):
                            auxs.append(AuxSettings.from_dict(aux_data))
        elif isinstance(auxs_raw, list):
            auxs = [AuxSettings.from_dict(a) for a in auxs_raw]

        return cls(
            pool=PoolSettings.from_dict(pool_data),
            ph=PhSettings.from_dict(ph_data),
            disinfection=DisinfectionSettings.from_dict(dis_data),
            water_level=WaterLevelSettings.from_dict(wl_data),
            filtrations=[FiltrationSettings.from_dict(f) for f in filt_data],
            auxs=auxs,
        )


# ---------------------------------------------------------------------------
# Equipments, History, Version
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EquipmentsInfo:
    """Equipment installation flags."""

    has_ph_sensor: bool = False
    has_orp_sensor: bool = False
    has_air_temperature_sensor: bool = False
    has_fac_sensor: bool = False
    has_conductivity_sensor: bool = False
    has_salt_sensor: bool = False
    has_water_level_sensor: bool = False
    has_fc_sensor: bool = False
    has_tc_sensor: bool = False
    has_flow_meter: bool = False
    has_energy_meter: bool = False
    has_pool_cover: bool = False
    has_jet_stream: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EquipmentsInfo:
        return cls(
            has_ph_sensor=data.get("hasPHSensor", False),
            has_orp_sensor=data.get("hasORPSensor", False),
            has_air_temperature_sensor=data.get("hasAirTemperatureSensor", False),
            has_fac_sensor=data.get("hasFACSensor", False),
            has_conductivity_sensor=data.get("hasConductivitySensor", False),
            has_salt_sensor=data.get("hasSaltSensor", False),
            has_water_level_sensor=data.get("hasWaterLevelSensor", False),
            has_fc_sensor=data.get("hasFCSensor", False),
            has_tc_sensor=data.get("hasTCSensor", False),
            has_flow_meter=data.get("hasFlowMeter", False),
            has_energy_meter=data.get("hasEnergyMeter", False),
            has_pool_cover=data.get("hasPoolCover", False),
            has_jet_stream=data.get("hasJetStream", False),
        )


@dataclass(frozen=True)
class DeviceHistory:
    """Device history timestamps."""

    last_ph_measure_date: str | None = None
    last_refill_date: str | None = None
    last_backwash_date: str | None = None
    ph_last_injection_duration: str | None = None
    disinfection_last_injection_duration: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceHistory:
        return cls(
            last_ph_measure_date=data.get("lastpHMeasureDate"),
            last_refill_date=data.get("lastRefillDate"),
            last_backwash_date=data.get("lastBackwashDate"),
            ph_last_injection_duration=data.get("pHLastInjectionDuration"),
            disinfection_last_injection_duration=data.get(
                "disinfectionLastInjectionDuration"
            ),
        )


@dataclass(frozen=True)
class VersionInfo:
    """Device version information."""

    poolcop_version: str = ""
    model: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VersionInfo:
        return cls(
            poolcop_version=data.get("poolCopVersion", ""),
            model=data.get("model", ""),
        )


# ---------------------------------------------------------------------------
# Top-level models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DeviceMinimalistic:
    """Minimal device info as returned in pool listings."""

    id: int
    nickname: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceMinimalistic:
        return cls(
            id=data.get("id", 0),
            nickname=data.get("nickname", ""),
        )


@dataclass(frozen=True)
class Pool:
    """Represents a pool."""

    id: int
    nickname: str | None = None
    address1: str | None = None
    address2: str | None = None
    zip_code: str | None = None
    city: str | None = None
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None
    creation_date: str | None = None
    devices: list[DeviceMinimalistic] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Pool:
        devs_raw = data.get("devices") or []
        return cls(
            id=data.get("id", 0),
            nickname=data.get("nickname"),
            address1=data.get("address1"),
            address2=data.get("address2"),
            zip_code=data.get("zipCode"),
            city=data.get("city"),
            country=data.get("country"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            timezone=data.get("timezone"),
            creation_date=data.get("creationDate"),
            devices=[DeviceMinimalistic.from_dict(d) for d in devs_raw],
        )


@dataclass(frozen=True)
class PoolCopDevice:
    """Full PoolCop device including state, settings, history, and equipments."""

    id: int
    nickname: str | None = None
    uuid: str | None = None
    mac: str | None = None
    installation_date: str | None = None
    connection_date: str | None = None
    last_ping: str | None = None
    is_fully_connected: bool = False
    cloud_access_state: str = ""
    state: DeviceState = field(default_factory=DeviceState)
    settings: DeviceSettings = field(default_factory=DeviceSettings)
    equipments_info: EquipmentsInfo = field(default_factory=EquipmentsInfo)
    history: DeviceHistory = field(default_factory=DeviceHistory)
    version_info: VersionInfo = field(default_factory=VersionInfo)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolCopDevice:
        """Create a PoolCopDevice from an API response dict."""
        state_data = data.get("state") or {}
        settings_data = data.get("settings") or {}
        equip_data = data.get("equipmentsInfo") or {}
        history_data = data.get("history") or {}
        version_data = data.get("versionInfo") or {}
        return cls(
            id=data.get("id", 0),
            nickname=data.get("nickname"),
            uuid=data.get("uuid"),
            mac=data.get("mac"),
            installation_date=data.get("installationDate"),
            connection_date=data.get("connectionDate"),
            last_ping=data.get("lastPing"),
            is_fully_connected=data.get("isFullyConnected", False),
            cloud_access_state=data.get("cloudAccessState", ""),
            state=DeviceState.from_dict(state_data),
            settings=DeviceSettings.from_dict(settings_data),
            equipments_info=EquipmentsInfo.from_dict(equip_data),
            history=DeviceHistory.from_dict(history_data),
            version_info=VersionInfo.from_dict(version_data),
        )


@dataclass(frozen=True)
class PoolCopCommand:
    """Represents a command sent to a PoolCop."""

    id: int
    device_id: int = 0
    user: str = ""
    label: str | None = None
    command_date: str | None = None
    delivery_date: str | None = None
    confirmation_date: str | None = None
    is_delivered: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolCopCommand:
        """Create a PoolCopCommand from an API response dict."""
        return cls(
            id=data.get("id", 0),
            device_id=data.get("deviceId", 0),
            user=data.get("user", ""),
            label=data.get("label"),
            command_date=data.get("commandDate"),
            delivery_date=data.get("deliveryDate"),
            confirmation_date=data.get("confirmationDate"),
            is_delivered=data.get("isDelivered", False),
        )
