"""The Ask Bert Conversation integration."""
from __future__ import annotations

import aiohttp
import asyncio
import async_timeout

import logging
import requests

from functools import partial
from typing import Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, MATCH_ALL
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, TemplateError
from homeassistant.helpers import intent, template
from homeassistant.util import ulid
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    CONF_CHAT_MODEL,
    CONF_MAX_TOKENS,
    CONF_PROMPT,
    CONF_TEMPERATURE,
    CONF_TOP_P,
    CONF_BASE_URL,
    DEFAULT_CHAT_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_PROMPT,
    DEFAULT_TEMPERATURE,
    DEFAULT_TOP_P,
    DEFAULT_BASE_URL,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ask Bert Conversation from a config entry."""
    #_key = entry.data[CONF_API_KEY]
    # api_base = entry.data[CONF_BASE_URL]

    #try:
    #    await hass.async_add_executor_job(
    #        partial(openai.Model.list)
    #    )
    #except error.AuthenticationError as err:
    #    _LOGGER.error("Invalid API key: %s", err)
    #    return False
    #except error.OpenAIError as err:
    #    raise ConfigEntryNotReady(err) from err

    conversation.async_set_agent(hass, entry, AskBertAgent(hass, entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Ask Bert."""
    #api_key = None
    #api_base = DEFAULT_BASE_URL
    conversation.async_unset_agent(hass, entry)
    return True


class AskBertAgent(conversation.AbstractConversationAgent):
    """Ask Bert conversation agent."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the agent."""
        self.hass = hass
        self.entry = entry
        self.history: dict[str, list[dict]] = {}

    @property
    def attribution(self):
        """Return the attribution."""
        return {"name": "Powered by Ask Bert", "url": "https://github.com/kerryland/askbert"}

    @property
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return MATCH_ALL

    async def async_process(
        self, user_input: conversation.ConversationInput
    ) -> conversation.ConversationResult:
        """Process a sentence."""
        raw_prompt = self.entry.options.get(CONF_PROMPT, DEFAULT_PROMPT)
        model = self.entry.options.get(CONF_CHAT_MODEL, DEFAULT_CHAT_MODEL)
        max_tokens = self.entry.options.get(CONF_MAX_TOKENS, DEFAULT_MAX_TOKENS)
        top_p = self.entry.options.get(CONF_TOP_P, DEFAULT_TOP_P)
        temperature = self.entry.options.get(CONF_TEMPERATURE, DEFAULT_TEMPERATURE)

        if user_input.conversation_id in self.history:
            conversation_id = user_input.conversation_id
            messages = self.history[conversation_id]
        else:
            conversation_id = ulid.ulid()
            try:
                prompt = self._async_generate_prompt(raw_prompt)
            except TemplateError as err:
                _LOGGER.error("Error rendering prompt: %s", err)
                intent_response = intent.IntentResponse(language=user_input.language)
                intent_response.async_set_error(
                    intent.IntentResponseErrorCode.UNKNOWN,
                    f"Sorry, I had a problem with my template: {err}",
                )
                return conversation.ConversationResult(
                    response=intent_response, conversation_id=conversation_id
                )
            messages = [{"role": "system", "content": prompt}]

        messages.append({"role": "user", "content": user_input.text})

        _LOGGER.debug("Prompt for %s: %s", model, messages)

#       try:
#           result = await openai.ChatCompletion.acreate(
#               model=model,
#               messages=messages,
#               max_tokens=max_tokens,
#               top_p=top_p,
#               temperature=temperature,
#               user=conversation_id,
#           )
#       except error.OpenAIError as err:
#           intent_response = intent.IntentResponse(language=user_input.language)
#           intent_response.async_set_error(
#               intent.IntentResponseErrorCode.UNKNOWN,
#               f"Sorry, I had a problem talking to Custom OpenAI compatible server: {err}",
#           )
#           return conversation.ConversationResult(
#               response=intent_response, conversation_id=conversation_id
#           )

#       _LOGGER.debug("Response %s", result)
#       response = result["choices"][0]["message"]

        api_url = 'http://192.168.1.4:5931/ask'
        params = {'q': user_input.text}

        try:
            async with async_timeout.timeout(10):
                session = async_get_clientsession(self.hass)
                async with session.get(api_url, params=params) as r:
                    if r.status != 200:
                        _LOGGER.error("Error fetching data from %s: %s", api_url, r.status)
                        return
                    data = await r.json()
                    _LOGGER.debug("Received data: %s", data)
                    response = data.get("message")
                    messages.append(response)
                    self.history[conversation_id] = messages

                    intent_response = intent.IntentResponse(language=user_input.language)
                    intent_response.async_set_speech(response)

                    return conversation.ConversationResult(
                        response=intent_response, conversation_id=conversation_id
                    )
                 
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching data from %s", api_url)
        except aiohttp.ClientError as err:
            _LOGGER.error("Client error fetching data from %s: %s", api_url, err)



    def _async_generate_prompt(self, raw_prompt: str) -> str:
        """Generate a prompt for the user."""
        return template.Template(raw_prompt, self.hass).async_render(
            {
                "ha_name": self.hass.config.location_name,
            },
            parse_result=False,
        )
