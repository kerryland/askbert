"""The Ask Bert Conversation integration."""
from __future__ import annotations

import aiohttp
import asyncio
import async_timeout
import json

import logging
import requests
import voluptuous as vol

from functools import partial
from typing import Literal

from homeassistant.components import conversation
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, MATCH_ALL
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import callback
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, TemplateError
from homeassistant.helpers import intent, template
from homeassistant.helpers.service import async_get_all_descriptions
from homeassistant.util import ulid
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import entity_registry as er

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

from .sentence_builder import SentenceBuilder

_LOGGER = logging.getLogger(__name__)

sentenceBuilder = SentenceBuilder()


def exportServices(hass):
    _LOGGER.debug("Exporting Services")
    services = hass.services.async_services()

    for domain, service_info in services.items():
        for service, info in service_info.items():
           _LOGGER.debug(f"Found {domain} -- {service}")



def exportEntity(hass, target_entity_id, system_descriptions):

    def plunkDown(serviceType):
        ctype = None
        command = None

        # TODO: These are platform-level commands that apply to the platform as whole
        # not to each entity exposed by the platform (aka integration)
        #if platform in system_descriptions and service_name in system_descriptions[platform]:
        #    command = system_descriptions[platform][service_name]
        #    ctype = "p (" + platform + ")"

        if domain in system_descriptions and service_name in system_descriptions[domain]:
            command = system_descriptions[domain][service_name]
            ctype = "d (" + domain + ")"

        if command:
            _LOGGER.debug(f"Command: {serviceType}-{ctype}.  {service_name}:  {command['name']}")

            sentenceBuilder.buildFromEntity(entity, entity_name, domain, service_name,
                                            command['name'], command['fields'].items())
        else:
            _LOGGER.warn(f"Unknown Command: {service_name} in {platform} or {domain}")
    
    entity_registry = er.async_get(hass)
    entity = hass.states.get(target_entity_id)
    entity_name = None
    if entity:
        entity_name = entity.attributes.get("friendly_name", None)

    # For 'platform'
    entity = entity_registry.async_get(target_entity_id)

    if not entity:
        _LOGGER.warn(f"No entity found! {target_entity_id}")
        return

    if entity.disabled_by != None:
        return


    if not entity_name or entity_name == '':
        entity_name  = entity.entity_id.split(".")[1].replace("_", " ")


    #_LOGGER.info("entity")
    #_LOGGER.info(dir(entity))

    #_LOGGER.info("entity_entry")
    #_LOGGER.info(dir(entity_entry))

    #entity_domain = entity["entity_id"].split(".")[0]
    #entity_name  = entity["entity_id"].split(".")[1]

    domain = target_entity_id.split(".")[0]
    platform = entity.platform

    # exportServices(hass)
    domain_services = hass.services.async_services_for_domain(domain)

    for service_name, service_info in domain_services.items():
        plunkDown("ds")

    # TODO: Deal with integration services, which can duplicate domain services
    #integration_services = hass.services.async_services_for_domain(entity.platform)
    #for service_name, service_info in integration_services.items():
    #    plunkDown("is")



async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ask Bert Conversation from a config entry."""
    #_key = entry.data[CONF_API_KEY]
    api_base = entry.data[CONF_BASE_URL]


    #try:
    #    await hass.async_add_executor_job(
    #        partial(openai.Model.list)
    #    )
    #except error.AuthenticationError as err:
    #    _LOGGER.error("Invalid API key: %s", err)
    #    return False
    #except error.OpenAIError as err:
    #    raise ConfigEntryNotReady(err) from err

    exposed_entities = []

    conversation.async_set_agent(hass, entry, AskBertAgent(hass, entry))


    async def handle_hass_started(event):
        """Handle Home Assistant started event."""
        _LOGGER.info("Home Assistant is fully set up and ready.")
        entity_registry = er.async_get(hass)

        system_descriptions = await async_get_all_descriptions(hass)

        # scripts are stored very weirdly in home assistant
        # so process them as a special case
        # scripts = system_descriptions['script']


        del system_descriptions['script']
        #system_descriptions['script'] = {'execute':{'name':"Execute",'description':'Run the script'}}

        # could just remove "turn_off", "turn_on", reload and  "toggle" (retaining "trigger")
        del system_descriptions['automation']
        

        #_LOGGER.info(dir(descriptions))
        #_LOGGER.info(json.dumps(descriptions))


        for entity_id, entity_entry in entity_registry.entities.items():
            # TODO: Reinstate! 
            #if entity_entry.options.get('conversation', {}).get('should_expose'):
                exposed_entities.append(entity_id)
                # TODO: Use entity_entry directly, not entity_id
                exportEntity(hass, entity_id, system_descriptions)

        #_LOGGER.info("Total exposed entities: %d", len(exposed_entities))

        jsonOutputPath = hass.config.path("tmp")
        _LOGGER.debug("Calling Dumping json to " + jsonOutputPath)

        await sentenceBuilder.adumpJson(jsonOutputPath)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, handle_hass_started)


 
    @callback
    def handle_entity_registry_updated(event):
        """Handle entity registry updated event."""
        action = event.data.get('action')
        entity_id = event.data.get('entity_id')
        
        entity_registry = er.async_get(hass)
        if action == "create" or action == "update":
            entity_entry = entity_registry.async_get(entity_id)

            # TODO. Remove
            exposed_entities.append(entity_id)

            # TODO. Reinstate
            #if entity_entry.options.get('conversation', {}).get('should_expose'):
            #    exposed_entities.append(entity_id)
            #    _LOGGER.info("Entity exposed to conversation agent: %s", entity_id)
            #else:
            #    exposed_entities.remove(entity_id)
            #    _LOGGER.info("Entity removed from conversation agent: %s", entity_id)

        elif action == "remove":
            exposed_entities.remove(entity_id)
            _LOGGER.info("Entity removed: %s", entity_id)


    # Register the event listener for entity registry updates
    hass.bus.async_listen("entity_registry_updated", handle_entity_registry_updated)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload Ask Bert."""
    #api_key = None
    api_base = DEFAULT_BASE_URL
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

        api_base = self.entry.data[CONF_BASE_URL]
        api_url = api_base + '/ask'
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


