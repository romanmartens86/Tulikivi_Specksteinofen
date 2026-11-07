"""The Tulikivi Specksteinofen integration."""
from __future__ import annotations

import logging
import os
import shutil
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, CONF_FLUE_SENSOR, CONF_STONE_SENSOR, CONF_ROOM_SENSOR
from .coordinator import TulikiviDataCoordinator

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH, Platform.NUMBER]

_LOGGER = logging.getLogger(__name__)

URL_CARD = "/tulikivi_specksteinofen/tulikivi-specksteinofen-card.js"


async def _async_register_frontend(hass: HomeAssistant) -> None:
    """Register frontend card and ensure Lovelace resource is served."""
    card_path = os.path.join(os.path.dirname(__file__), "tulikivi-specksteinofen-card.js")
    if not os.path.exists(card_path):
        return

    # 1. Register static path with Home Assistant HTTP
    try:
        from homeassistant.components.http import StaticPathConfig
        await hass.http.async_register_static_paths([
            StaticPathConfig(URL_CARD, card_path, False)
        ])
        _LOGGER.info("Registered static path %s for Tulikivi Card", URL_CARD)
    except Exception as err:
        _LOGGER.debug("Could not register static path via StaticPathConfig: %s", err)
        try:
            hass.http.register_static_path(URL_CARD, card_path, cache_headers=False)
        except Exception:
            pass

    # 2. Also copy to /config/www/ so /local/tulikivi-specksteinofen-card.js works as fallback
    try:
        www_dir = hass.config.path("www")
        os.makedirs(www_dir, exist_ok=True)
        dest = os.path.join(www_dir, "tulikivi-specksteinofen-card.js")
        shutil.copy2(card_path, dest)
    except Exception as err:
        _LOGGER.debug("Could not copy card to www: %s", err)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Tulikivi Specksteinofen from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    if "_frontend_registered" not in hass.data[DOMAIN]:
        await _async_register_frontend(hass)
        hass.data[DOMAIN]["_frontend_registered"] = True

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
