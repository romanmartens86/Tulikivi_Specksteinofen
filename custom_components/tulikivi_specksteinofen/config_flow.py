"""Config flow for Tulikivi Specksteinofen integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_FLUE_SENSOR,
    CONF_STONE_SENSOR,
    CONF_MASS,
    CONF_ROOM_TEMP,
    CONF_MAX_TEMP,
    CONF_AUTO_LEARN,
    DEFAULT_NAME,
    DEFAULT_MASS,
    DEFAULT_ROOM_TEMP,
    DEFAULT_MAX_TEMP,
    DEFAULT_AUTO_LEARN,
)

class TulikiviConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tulikivi Specksteinofen."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get("name", DEFAULT_NAME),
                data=user_input,
            )

        schema = vol.Schema(
            {
                vol.Required("name", default=DEFAULT_NAME): cv.string,
                vol.Required(CONF_FLUE_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_STONE_SENSOR): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain="sensor")
                ),
                vol.Required(CONF_MASS, default=DEFAULT_MASS): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=100, max=6000, step=25, unit_of_measurement="kg", mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(CONF_ROOM_TEMP, default=DEFAULT_ROOM_TEMP): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=10, max=30, step=0.5, unit_of_measurement="°C", mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(CONF_MAX_TEMP, default=DEFAULT_MAX_TEMP): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=40, max=120, step=1, unit_of_measurement="°C", mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(CONF_AUTO_LEARN, default=DEFAULT_AUTO_LEARN): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return TulikiviOptionsFlowHandler(config_entry)


class TulikiviOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Tulikivi Specksteinofen."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            # Update config entry data
            new_data = {**self.config_entry.data, **user_input}
            self.hass.config_entries.async_update_entry(self.config_entry, data=new_data)
            return self.async_create_entry(title="", data={})

        current = self.config_entry.data

        schema = vol.Schema(
            {
                vol.Required(CONF_MASS, default=current.get(CONF_MASS, DEFAULT_MASS)): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=100, max=6000, step=25, unit_of_measurement="kg", mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(CONF_ROOM_TEMP, default=current.get(CONF_ROOM_TEMP, DEFAULT_ROOM_TEMP)): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=10, max=30, step=0.5, unit_of_measurement="°C", mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(CONF_MAX_TEMP, default=current.get(CONF_MAX_TEMP, DEFAULT_MAX_TEMP)): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=40, max=120, step=1, unit_of_measurement="°C", mode=selector.NumberSelectorMode.BOX
                    )
                ),
                vol.Required(CONF_AUTO_LEARN, default=current.get(CONF_AUTO_LEARN, DEFAULT_AUTO_LEARN)): selector.BooleanSelector(),
            }
        )

        return self.async_show_form(step_id="init", data_schema=schema)
