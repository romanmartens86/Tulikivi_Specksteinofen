"""Number platform for Tulikivi Specksteinofen integration."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import TulikiviDataCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Tulikivi number entities from a config entry."""
    coordinator: TulikiviDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get("name", DEFAULT_NAME)

    async_add_entities([TulikiviMaxTempNumber(coordinator, name, entry)])


class TulikiviMaxTempNumber(NumberEntity):
    """Number entity to view and set the 100% maximum stone temperature."""

    _attr_has_entity_name = True
    _attr_name = "Maximale Speichertemperatur"
    _attr_icon = "mdi:thermometer-high"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = 40.0
    _attr_native_max_value = 120.0
    _attr_native_step = 1.0
    _attr_mode = NumberMode.BOX

    def __init__(
        self, coordinator: TulikiviDataCoordinator, base_name: str, entry: ConfigEntry
    ) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_max_temp_number"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=base_name,
            manufacturer="Tulikivi",
            model="Specksteinofen (Speicher)",
        )

    async def async_added_to_hass(self) -> None:
        self.coordinator.register_listener(self.async_write_ha_state)

    @property
    def native_value(self) -> float:
        return self.coordinator.max_temp

    async def async_set_native_value(self, value: float) -> None:
        """Update maximum temperature."""
        await self.coordinator.async_set_max_temp(value)

