"""The Tulikivi Specksteinofen integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_FLUE_SENSOR, CONF_STONE_SENSOR, CONF_ROOM_SENSOR
from .coordinator import TulikiviDataCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tulikivi Specksteinofen from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    coordinator = TulikiviDataCoordinator(hass, entry)
    hass.data[DOMAIN][entry.entry_id] = coordinator

    sensors_to_track = [
        sid
        for sid in (
            entry.data.get(CONF_FLUE_SENSOR),
            entry.data.get(CONF_STONE_SENSOR),
            entry.data.get(CONF_ROOM_SENSOR),
        )
        if sid
    ]
    await coordinator.async_setup(sensors_to_track)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Listen for options updates
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options are updated."""
    coordinator: TulikiviDataCoordinator | None = hass.data.get(DOMAIN, {}).get(entry.entry_id)
    if coordinator and coordinator.is_internal_update:
        return
    await hass.config_entries.async_reload(entry.entry_id)
