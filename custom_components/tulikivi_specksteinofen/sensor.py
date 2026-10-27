"""Sensor platform for Tulikivi Specksteinofen integration."""
from __future__ import annotations

import logging
from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfTime
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    DOMAIN,
    CONF_FLUE_SENSOR,
    CONF_STONE_SENSOR,
    CONF_ROOM_SENSOR,
    CONF_MASS,
    CONF_ROOM_TEMP,
    CONF_MAX_TEMP,
    CONF_AUTO_LEARN,
    DEFAULT_NAME,
    DEFAULT_MASS,
    DEFAULT_ROOM_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_AUTO_LEARN,
    SPECIFIC_HEAT_CAPACITY,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tulikivi sensors from a config entry."""
    data = entry.data

    flue_sensor_id = data.get(CONF_FLUE_SENSOR)
    stone_sensor_id = data.get(CONF_STONE_SENSOR)
    room_sensor_id = data.get(CONF_ROOM_SENSOR)
    name = data.get("name", DEFAULT_NAME)

    coordinator = TulikiviDataCoordinator(hass, entry)

    entities = [
        TulikiviStoragePercentSensor(coordinator, name, entry),
        TulikiviEnergySensor(coordinator, name, entry),
        TulikiviMaxCapacitySensor(coordinator, name, entry),
        TulikiviStatusSensor(coordinator, name, entry),
        TulikiviRemainingHoursSensor(coordinator, name, entry),
    ]

    async_add_entities(entities)
    sensors_to_track = [sid for sid in (flue_sensor_id, stone_sensor_id, room_sensor_id) if sid]
    await coordinator.async_setup(sensors_to_track)


class TulikiviDataCoordinator:
    """Coordinates reading state changes from the flue, stone, and room sensors."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.listeners = []
        self.flue_temp = 20.0
        self.stone_temp = 20.0
        self.live_room_temp: float | None = None

    @property
    def mass(self) -> float:
        return float(self.entry.data.get(CONF_MASS, DEFAULT_MASS))

    @property
    def room_temp(self) -> float:
        if self.live_room_temp is not None:
            return self.live_room_temp
        return float(self.entry.data.get(CONF_ROOM_TEMP, DEFAULT_ROOM_TEMP))

    @property
    def max_temp(self) -> float:
        return float(self.entry.data.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP))

    @property
    def auto_learn(self) -> bool:
        return bool(self.entry.data.get(CONF_AUTO_LEARN, DEFAULT_AUTO_LEARN))

    async def async_setup(self, sensor_ids: list[str]) -> None:
        """Register state change listeners for source temperature sensors."""
        @callback
        def _state_changed_event(event):
            entity_id = event.data.get("entity_id")
            new_state = event.data.get("new_state")
            if new_state is None or new_state.state in ("unknown", "unavailable"):
                return

            try:
                val = float(new_state.state)
                if entity_id == self.entry.data.get(CONF_FLUE_SENSOR):
                    self.flue_temp = val
                elif entity_id == self.entry.data.get(CONF_STONE_SENSOR):
                    self.stone_temp = val
                    self._check_auto_learn(val)
                elif entity_id == self.entry.data.get(CONF_ROOM_SENSOR):
                    self.live_room_temp = val

                self._notify_listeners()
            except ValueError:
                pass

        # Read initial states if available
        for sid in sensor_ids:
            state = self.hass.states.get(sid)
            if state and state.state not in ("unknown", "unavailable"):
                try:
                    val = float(state.state)
                    if sid == self.entry.data.get(CONF_FLUE_SENSOR):
                        self.flue_temp = val
                    elif sid == self.entry.data.get(CONF_STONE_SENSOR):
                        self.stone_temp = val
                    elif sid == self.entry.data.get(CONF_ROOM_SENSOR):
                        self.live_room_temp = val
                except ValueError:
                    pass

        self._notify_listeners()

        self.entry.async_on_unload(
            async_track_state_change_event(self.hass, sensor_ids, _state_changed_event)
        )

    def _check_auto_learn(self, current_stone_temp: float) -> None:
        """Auto-learn new peak temperature if stone reaches a new high."""
        if self.auto_learn and current_stone_temp > self.max_temp:
            new_max = round(current_stone_temp, 0)
            _LOGGER.info("Tulikivi auto-learned new peak stone temperature: %s °C", new_max)
            new_data = {**self.entry.data, CONF_MAX_TEMP: new_max}
            self.hass.config_entries.async_update_entry(self.entry, data=new_data)

            self.hass.components.persistent_notification.async_create(
                f"Der Specksteinofen hat einen neuen Höchstwert von {new_max} °C erreicht! Die 100%-Marke wurde angepasst.",
                title="🪵 Neuer Speicher-Höchstwert gelernt",
                notification_id="tulikivi_new_peak"
            )

    def register_listener(self, listener) -> None:
        self.listeners.append(listener)

    def _notify_listeners(self) -> None:
        for listener in self.listeners:
            listener()


class TulikiviBaseSensor(SensorEntity):
    """Base entity for Tulikivi sensors."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: TulikiviDataCoordinator, base_name: str, entry: ConfigEntry) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=base_name,
            manufacturer="Tulikivi",
            model="Specksteinofen (Speicher)",
        )

    async def async_added_to_hass(self) -> None:
        self.coordinator.register_listener(self.async_write_ha_state)


class TulikiviStoragePercentSensor(TulikiviBaseSensor):
    """Calculates storage charge percentage (0 - 100%)."""

    _attr_name = "Speicherladung"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:battery-charging-high"

    def __init__(self, coordinator, base_name, entry) -> None:
        super().__init__(coordinator, base_name, entry)
        self._attr_unique_id = f"{entry.entry_id}_storage_percent"

    @property
    def native_value(self) -> int:
        delta = self.coordinator.stone_temp - self.coordinator.room_temp
        max_delta = self.coordinator.max_temp - self.coordinator.room_temp
        if max_delta <= 0:
            return 0
        pct = (delta / max_delta) * 100.0
        return int(max(0, min(100, round(pct))))


class TulikiviEnergySensor(TulikiviBaseSensor):
    """Calculates stored thermal energy in kWh."""

    _attr_name = "Gespeicherte Wärme"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:fire-circle"

    def __init__(self, coordinator, base_name, entry) -> None:
        super().__init__(coordinator, base_name, entry)
        self._attr_unique_id = f"{entry.entry_id}_energy_kwh"

    @property
    def native_value(self) -> float:
        delta_t = max(0.0, self.coordinator.stone_temp - self.coordinator.room_temp)
        kwh = self.coordinator.mass * SPECIFIC_HEAT_CAPACITY * delta_t
        return round(kwh, 1)


class TulikiviMaxCapacitySensor(TulikiviBaseSensor):
    """Calculates maximum thermal capacity in kWh based on oven mass and max temp."""

    _attr_name = "Max. Speicherkapazität"
    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:battery-high"

    def __init__(self, coordinator, base_name, entry) -> None:
        super().__init__(coordinator, base_name, entry)
        self._attr_unique_id = f"{entry.entry_id}_max_capacity_kwh"

    @property
    def native_value(self) -> float:
        delta_max = max(0.0, self.coordinator.max_temp - self.coordinator.room_temp)
        kwh = self.coordinator.mass * SPECIFIC_HEAT_CAPACITY * delta_max
        return round(kwh, 1)


class TulikiviStatusSensor(TulikiviBaseSensor):
    """Calculates current operating state of the stove."""

    _attr_name = "Betriebsstatus"
    _attr_icon = "mdi:fireplace"

    def __init__(self, coordinator, base_name, entry) -> None:
        super().__init__(coordinator, base_name, entry)
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def native_value(self) -> str:
        flue = self.coordinator.flue_temp
        stone = self.coordinator.stone_temp
        room = self.coordinator.room_temp

        if flue >= 170.0:
            return "Voller Abbrand"
        if 80.0 <= flue < 170.0 and stone < (room + 15.0):
            return "Anheizen"
        if 70.0 <= flue < 150.0 and stone > (room + 10.0):
            return "Glutphase (Klappe schließen!)"
        if stone > (room + 3.0):
            return "Wärmeabgabe aktiv"
        return "Kalt / Aus"


class TulikiviRemainingHoursSensor(TulikiviBaseSensor):
    """Calculates remaining hours of sensible heat delivery."""

    _attr_name = "Restwärmedauer"
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_icon = "mdi:timer-sand"

    def __init__(self, coordinator, base_name, entry) -> None:
        super().__init__(coordinator, base_name, entry)
        self._attr_unique_id = f"{entry.entry_id}_remaining_hours"

    @property
    def native_value(self) -> float:
        delta_t = max(0.0, self.coordinator.stone_temp - self.coordinator.room_temp)
        mass = max(200.0, self.coordinator.mass)
        # Cooling rate scales with mass: 1000kg -> ~2.2 °C/h, 2600kg -> ~0.85 °C/h
        cooling_rate = 2.2 * (1000.0 / mass)
        hours = delta_t / cooling_rate
        return round(hours, 1)
