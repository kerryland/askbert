"""Config flow for OpenAI Conversation integration."""
from __future__ import annotations

from functools import partial
import logging
import types
from types import MappingProxyType
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    TemplateSelector,
)

from .const import (
    CONF_BASE_URL,
    DEFAULT_BASE_URL,
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
    }
)

DEFAULT_OPTIONS = types.MappingProxyType(
    {
        CONF_BASE_URL: DEFAULT_BASE_URL,
    }
)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> None:
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    # openai.api_key = data[CONF_API_KEY]
    # openai.api_base = data[CONF_BASE_URL]
    # await hass.async_add_executor_job(partial(openai.Model.list))


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenAI Conversation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        # try:
        #    await validate_input(self.hass, user_input)
        # except error.APIConnectionError:
        #    errors["base"] = "cannot_connect"
        # except error.AuthenticationError:
        #    errors["base"] = "invalid_auth"
        # except Exception:  # pylint: disable=broad-except
        #    _LOGGER.exception("Unexpected exception")
        #    errors["base"] = "unknown"
        # else:
        return self.async_create_entry(title="Sentence Transformer Conversation", data=user_input)

        # return self.async_show_form(
        #    step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        # )

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlow(config_entry)


class OptionsFlow(config_entries.OptionsFlow):
    """OpenAI config flow options handler."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="Sentence Transformer Conversation", data=user_input)
        schema = openai_config_option_schema(self.config_entry.options)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )


def openai_config_option_schema(options: MappingProxyType[str, Any]) -> dict:
    """Return a schema for OpenAI completion options."""
    if not options:
        options = DEFAULT_OPTIONS
    return {

    }
