"""Data coordinator for Tulikivi Specksteinofen integration."""
from __future__ import annotations

import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_FLUE_SENSOR,
    CONF_STONE_SENSOR,
    CONF_ROOM_SENSOR,
    CONF_MASS,
    CONF_ROOM_TEMP,
    CONF_MAX_TEMP,
    CONF_AUTO_LEARN,
    DEFAULT_MASS,
    DEFAULT_ROOM_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_AUTO_LEARN,
)

_LOGGER = logging.getLogger(__name__)


class TulikiviDataCoordinator:
    """Coordinates reading state changes and managing auto-learn logic."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.listeners = []
        self.flue_temp = 20.0
        self.stone_temp = 20.0
        self.live_room_temp: float | None = None
        self.is_internal_update = False

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

    async def async_set_auto_learn(self, enabled: bool) -> None:
        """Enable or disable auto-learn and persist to config entry."""
        if self.auto_learn == enabled:
            return
        _LOGGER.info("Tulikivi auto-learn set to: %s", enabled)
        new_data = {**self.entry.data, CONF_AUTO_LEARN: enabled}
        self.is_internal_update = True
        try:
            self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        finally:
            self.is_internal_update = False
        self._notify_listeners()

    async def async_set_max_temp(self, new_max: float) -> None:
        """Manually adjust max temperature and persist to config entry."""
        rounded = round(new_max, 1)
        if self.max_temp == rounded:
            return
        _LOGGER.info("Tulikivi max temperature updated to: %s °C", rounded)
        new_data = {**self.entry.data, CONF_MAX_TEMP: rounded}
        self.is_internal_update = True
        try:
            self.hass.config_entries.async_update_entry(self.entry, data=new_data)
        finally:
            self.is_internal_update = False
        self._notify_listeners()

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
            self.is_internal_update = True
            try:
                self.hass.config_entries.async_update_entry(self.entry, data=new_data)
            finally:
                self.is_internal_update = False

            self.hass.components.persistent_notification.async_create(
                f"Der Specksteinofen hat einen neuen Höchstwert von {new_max} °C erreicht! Die 100%-Marke wurde angepasst.\n\n"
                f"Tipp: Du kannst 'Auto-Learn' jetzt in den Einstellungen oder über den Schalter deaktivieren, um diesen Höchstwert dauerhaft festzusetzen.",
                title="🪵 Neuer Speicher-Höchstwert gelernt",
                notification_id="tulikivi_new_peak",
            )

    def register_listener(self, listener) -> None:
        self.listeners.append(listener)

    def _notify_listeners(self) -> None:
        for listener in self.listeners:
            listener()

