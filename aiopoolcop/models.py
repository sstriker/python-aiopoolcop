"""Data models for PoolCop Cloud API responses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PoolCopAlarm:
    """Represents a PoolCop alarm."""

    id: int
    pool_cop_id: int
    code: str | None = None
    severity: str = "Warning"
    label: str | None = None
    description: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    @property
    def is_active(self) -> bool:
        """Return True if the alarm is currently active."""
        return self.end_date is None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolCopAlarm:
        """Create a PoolCopAlarm from an API response dict."""
        return cls(
            id=data.get("id", 0),
            pool_cop_id=data.get("poolCopId", 0),
            code=data.get("code"),
            severity=data.get("severity", "Warning"),
            label=data.get("label"),
            description=data.get("description"),
            start_date=data.get("startDate"),
            end_date=data.get("endDate"),
        )


@dataclass(frozen=True)
class PumpInfo:
    """Represents pump state information."""

    id: int = 0
    current_speed: str = "None"
    forced_remaining: str = "00:00:00"
    running_status: str = "Stop"
    pump_state: bool = False
    pump_primed: bool = False
    valve_position: str = "Filter"
    pressure: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PumpInfo:
        """Create a PumpInfo from an API response dict."""
        return cls(
            id=data.get("id", 0),
            current_speed=data.get("pumpCurrentSpeed", "None"),
            forced_remaining=data.get("pumpForcedRemaining", "00:00:00"),
            running_status=data.get("runningStatus", "Stop"),
            pump_state=data.get("pumpState", False),
            pump_primed=data.get("pumpPrimed", False),
            valve_position=data.get("valvePosition", "Filter"),
            pressure=data.get("pumpPressure", 0.0),
        )


@dataclass(frozen=True)
class WaterLevelInfo:
    """Represents water level state information."""

    installed: bool = False
    state: str = "Normal"
    set_point: str = "Unknown"
    is_on_target: bool | None = None
    is_on_error: bool | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WaterLevelInfo:
        """Create a WaterLevelInfo from an API response dict."""
        return cls(
            installed=data.get("installed", False),
            state=data.get("state", "Normal"),
            set_point=data.get("setPoint", "Unknown"),
            is_on_target=data.get("isOnTarget"),
            is_on_error=data.get("isOnError"),
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
    """Represents flow visualizer state information."""

    installed: bool = False
    pump_id: int = 0
    low_value: float = 0.0
    high_value: float = 0.0
    flow_rate: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FlowVisInfo:
        """Create a FlowVisInfo from an API response dict."""
        return cls(
            installed=data.get("installed", False),
            pump_id=data.get("pumpId", 0),
            low_value=data.get("lowValue", 0.0),
            high_value=data.get("highValue", 0.0),
            flow_rate=data.get("flowRate", 0.0),
        )


def _parse_auxiliaries(data: dict[str, Any]) -> dict[str, dict[str, bool]]:
    """Parse auxiliaries from the state response.

    Returns a dict keyed by module name, each containing aux name -> bool.
    The API has auxiliariesUFLegacy/auxiliariesSatellite and a merged
    'auxiliaries' read-only field. We prefer 'auxiliaries' when available.
    """
    aux = data.get("auxiliaries")
    if aux is not None:
        return {
            module: {k: v for k, v in ports.items() if k != "None"}
            for module, ports in aux.items()
            if module != "None" and isinstance(ports, dict)
        }
    # Fall back to UF Legacy or Satellite
    for key in ("auxiliariesUFLegacy", "auxiliariesSatellite"):
        aux = data.get(key)
        if aux is not None:
            return {
                module: {k: v for k, v in ports.items() if k != "None"}
                for module, ports in aux.items()
                if module != "None" and isinstance(ports, dict)
            }
    return {}


def _parse_inputs(data: dict[str, Any]) -> dict[str, bool]:
    """Parse inputs from the state response.

    Returns a dict of input name -> bool.
    """
    inputs = data.get("inputs")
    if inputs is not None and isinstance(inputs, dict):
        return {k: v for k, v in inputs.items() if k != "None"}
    for key in ("inputsUFLegacy", "inputsSatellite"):
        inputs = data.get(key)
        if inputs is not None and isinstance(inputs, dict):
            return {k: v for k, v in inputs.items() if k != "None"}
    return {}


@dataclass(frozen=True)
class PoolCopState:
    """Represents the full state of a PoolCop device."""

    status: str = "Ready"
    pumps: list[PumpInfo] = field(default_factory=list)
    ph: float = 0.0
    orp: int = 0
    water_temperature: float = 0.0
    daily_average_water_temperature: float = 0.0
    air_temperature: float = 0.0
    battery_voltage: float = 0.0
    mains_voltage: float = 0.0
    mains_power_lost: bool = False
    free_available_chlorine: float = 0.0
    free_chlorine: float = 0.0
    total_chlorine: float = 0.0
    water_level: WaterLevelInfo = field(default_factory=WaterLevelInfo)
    pool_cover: PoolCoverInfo = field(default_factory=PoolCoverInfo)
    jet_stream: JetStreamInfo = field(default_factory=JetStreamInfo)
    flow_vis: list[FlowVisInfo] = field(default_factory=list)
    auxiliaries: dict[str, dict[str, bool]] = field(default_factory=dict)
    inputs: dict[str, bool] = field(default_factory=dict)
    date_time: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolCopState:
        """Create a PoolCopState from an API response dict."""
        pumps_data = data.get("pumpsInfo") or []
        wl_data = data.get("waterLevel") or {}
        pc_data = data.get("poolCover") or {}
        js_data = data.get("jetStream") or {}
        fv_data = data.get("flowVis") or []

        return cls(
            status=data.get("status", "Ready"),
            pumps=[PumpInfo.from_dict(p) for p in pumps_data],
            ph=data.get("pH", 0.0),
            orp=data.get("orp", 0),
            water_temperature=data.get("waterTemperature", 0.0),
            daily_average_water_temperature=data.get(
                "dailyAverageWaterTemperature", 0.0
            ),
            air_temperature=data.get("airTemperature", 0.0),
            battery_voltage=data.get("batteryVoltage", 0.0),
            mains_voltage=data.get("mainsVoltage", 0.0),
            mains_power_lost=data.get("mainsPowerLost", False),
            free_available_chlorine=data.get("freeAvailableChlorine", 0.0),
            free_chlorine=data.get("freeChlorine", 0.0),
            total_chlorine=data.get("totalChlorine", 0.0),
            water_level=WaterLevelInfo.from_dict(wl_data),
            pool_cover=PoolCoverInfo.from_dict(pc_data),
            jet_stream=JetStreamInfo.from_dict(js_data),
            flow_vis=[FlowVisInfo.from_dict(f) for f in fv_data],
            auxiliaries=_parse_auxiliaries(data),
            inputs=_parse_inputs(data),
            date_time=data.get("dateTime", ""),
        )


@dataclass(frozen=True)
class PoolCopSummary:
    """Summary information about a PoolCop device."""

    id: int
    nickname: str | None = None
    uuid: str | None = None
    mac: str | None = None
    pool_id: int | None = None
    user_id: int | None = None
    is_connected: bool = False
    is_fully_connected: bool = False
    connection_date: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolCopSummary:
        """Create a PoolCopSummary from an API response dict."""
        return cls(
            id=data.get("id", 0),
            nickname=data.get("nickname"),
            uuid=data.get("uuid"),
            mac=data.get("mac"),
            pool_id=data.get("poolId"),
            user_id=data.get("userId"),
            is_connected=data.get("isConnected", False),
            is_fully_connected=data.get("isFullyConnected", False),
            connection_date=data.get("connectionDate"),
        )


@dataclass(frozen=True)
class PoolCopDevice:
    """Full PoolCop device information including state."""

    id: int
    nickname: str | None = None
    uuid: str | None = None
    mac: str | None = None
    pool_id: int | None = None
    user_id: int | None = None
    is_connected: bool = False
    is_fully_connected: bool = False
    connection_date: str | None = None
    state: PoolCopState = field(default_factory=PoolCopState)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolCopDevice:
        """Create a PoolCopDevice from an API response dict."""
        state_data = data.get("state") or {}
        return cls(
            id=data.get("id", 0),
            nickname=data.get("nickname"),
            uuid=data.get("uuid"),
            mac=data.get("mac"),
            pool_id=data.get("poolId"),
            user_id=data.get("userId"),
            is_connected=data.get("isConnected", False),
            is_fully_connected=data.get("isFullyConnected", False),
            connection_date=data.get("connectionDate"),
            state=PoolCopState.from_dict(state_data),
        )


@dataclass(frozen=True)
class Pool:
    """Represents a pool."""

    id: int
    nickname: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    timezone: str | None = None
    city: str | None = None
    country: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Pool:
        """Create a Pool from an API response dict."""
        return cls(
            id=data.get("id", 0),
            nickname=data.get("nickname"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            timezone=data.get("timezone"),
            city=data.get("city"),
            country=data.get("country"),
        )


@dataclass(frozen=True)
class UserProfile:
    """Represents the authenticated user's profile."""

    id: int
    email: str | None = None
    firstname: str | None = None
    lastname: str | None = None
    timezone: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> UserProfile:
        """Create a UserProfile from an API response dict."""
        return cls(
            id=data.get("id", 0),
            email=data.get("email"),
            firstname=data.get("firstname"),
            lastname=data.get("lastname"),
            timezone=data.get("timezone"),
        )


@dataclass(frozen=True)
class PoolCopCommand:
    """Represents a command sent to a PoolCop."""

    id: int
    pool_cop_id: int = 0
    label: str | None = None
    command_date: str | None = None
    delivery_date: str | None = None
    confirmation_date: str | None = None
    is_delivered: bool = False
    return_code: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolCopCommand:
        """Create a PoolCopCommand from an API response dict."""
        return cls(
            id=data.get("id", 0),
            pool_cop_id=data.get("poolCopId", 0),
            label=data.get("label"),
            command_date=data.get("commandDate"),
            delivery_date=data.get("deliveryDate"),
            confirmation_date=data.get("confirmationDate"),
            is_delivered=data.get("isDelivered", False),
            return_code=data.get("returnCode"),
        )


@dataclass(frozen=True)
class PoolCopAuxiliary:
    """Represents a PoolCop auxiliary port configuration."""

    aux_channel: int = 0
    module_id: int = 0
    mode: str | None = None
    label: str | None = None
    friendly_name: str | None = None
    is_reserved: bool = False
    status: bool = False
    has_timer: bool = False
    is_heating: bool = False
    heating_set_point: float | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PoolCopAuxiliary:
        """Create a PoolCopAuxiliary from an API response dict."""
        return cls(
            aux_channel=data.get("auxChannel", 0),
            module_id=data.get("moduleId", 0),
            mode=data.get("mode"),
            label=data.get("label"),
            friendly_name=data.get("friendlyName"),
            is_reserved=data.get("isReserved", False),
            status=data.get("status", False),
            has_timer=data.get("hasTimer", False),
            is_heating=data.get("isHeating", False),
            heating_set_point=data.get("heatingSetPoint"),
        )


@dataclass(frozen=True)
class DataPoint:
    """Represents a time-series data point."""

    timestamp: str = ""
    value: float | str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DataPoint:
        """Create a DataPoint from an API response dict."""
        return cls(
            timestamp=data.get("timestamp", ""),
            value=data.get("value"),
        )


@dataclass(frozen=True)
class DisconnectionTime:
    """Represents a disconnection time window."""

    start: str = ""
    end: str = ""
    duration: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DisconnectionTime:
        """Create a DisconnectionTime from an API response dict."""
        return cls(
            start=data.get("start", ""),
            end=data.get("end", ""),
            duration=data.get("duration", ""),
        )


@dataclass(frozen=True)
class WeatherCondition:
    """Represents current weather data."""

    temp_c: float = 0.0
    humidity: int = 0
    condition_text: str = ""
    wind_kph: float = 0.0
    uv: float = 0.0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> WeatherCondition:
        """Create a WeatherCondition from an API response dict."""
        current = data.get("current", data)
        condition = current.get("condition", {})
        return cls(
            temp_c=current.get("temp_c", 0.0),
            humidity=current.get("humidity", 0),
            condition_text=condition.get("text", ""),
            wind_kph=current.get("wind_kph", 0.0),
            uv=current.get("uv", 0.0),
        )
