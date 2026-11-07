"""Switch platform for Tulikivi Specksteinofen integration."""
from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
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
    """Set up Tulikivi switch from a config entry."""
    coordinator: TulikiviDataCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data.get("name", DEFAULT_NAME)

    async_add_entities([TulikiviAutoLearnSwitch(coordinator, name, entry)])


class TulikiviAutoLearnSwitch(SwitchEntity):
    """Switch to toggle automatic learning of maximum stone temperature."""

    _attr_has_entity_name = True
    _attr_name = "Automatisches Lernen (Auto-Learn)"
    _attr_icon = "mdi:school"

    def __init__(
        self, coordinator: TulikiviDataCoordinator, base_name: str, entry: ConfigEntry
    ) -> None:
        self.coordinator = coordinator
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_auto_learn_switch"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=base_name,
            manufacturer="Tulikivi",
            model="Specksteinofen (Speicher)",
        )

    async def async_added_to_hass(self) -> None:
        self.coordinator.register_listener(self.async_write_ha_state)

    @property
    def is_on(self) -> bool:
        return self.coordinator.auto_learn

    async def async_turn_on(self, **kwargs) -> None:
        """Turn auto-learn on."""
        await self.coordinator.async_set_auto_learn(True)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn auto-learn off (freezing the peak temperature)."""
        await self.coordinator.async_set_auto_learn(False)

