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
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DEFAULT_NAME, SPECIFIC_HEAT_CAPACITY
from .coordinator import TulikiviDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tulikivi sensors from a config entry."""
    coordinator: TulikiviDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get("name", DEFAULT_NAME)

    entities = [
        TulikiviStoragePercentSensor(coordinator, name, entry),
        TulikiviEnergySensor(coordinator, name, entry),
        TulikiviMaxCapacitySensor(coordinator, name, entry),
        TulikiviStatusSensor(coordinator, name, entry),
        TulikiviRemainingHoursSensor(coordinator, name, entry),
    ]

    async_add_entities(entities)


class TulikiviBaseSensor(SensorEntity):
    """Base entity for Tulikivi sensors."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: TulikiviDataCoordinator, base_name: str, entry: ConfigEntry
    ) -> None:
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
    """Calculates storage charge percentage (can exceed 100% on heavy firing)."""

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
        # No cap at 100%: can exceed 100% when heated heavily above calibrated peak
        return int(max(0, round(pct)))


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
