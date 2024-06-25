
import logging
import json
import asyncio
import aiofiles

_LOGGER = logging.getLogger(__name__)

class SentenceBuilder() :

	# This ends up as a blob of json sent to the server. It is a list containing:
    # - entityDescription, service, entity_id 

    word_service = []

    def recordWords(self, identifyingWords, name) -> bool :
        if (name != None):
           for word in name.split():
               identifyingWords.add(word.lower())
           return True
        return False


    def recordService(self, identifyingWords, entity, service, command, fields):
        self.recordWords(identifyingWords, entity.attributes.get("friendly_name", None))
        self.recordWords(identifyingWords, entity.name)
        self.recordWords(identifyingWords, command)
        
        for field, field_properties in fields:
            if field_properties.get("required", False):
               self.recordWords(identifyingWords, ">" + field + "<")

        entityDescription = ""
        for word in identifyingWords:
            entityDescription += word + " "


        _LOGGER.debug(entityDescription)
        
        # TODO: Why is entityDescription a string rather than keep as a set?
        pair = [ entityDescription, service, entity.entity_id ]
        self.word_service.append(pair)
        identifyingWords.clear()


    entityNames = {}
    entityByDomain = {} # dictionary
    sentenceByDomain = {} # dictionary
    fakeSentences = [
       "switch the bedroom light on",
       "make it warmer in the dining room",
       "kitchen lights off",
            ] # List


    def add_item(self, target, key, value):
        if not key in target:
            target[key] = set([])

        target[key].add(value)


    def logForExperiment(self, identifyingWords, entity, entityName, domain, service, command, fields):
        #self.recordWords(identifyingWords, entity.attributes.get("friendly_name", None))
        # TODO: Check if name ever differs from friendly name (it does!!!)
        self.recordWords(identifyingWords, entityName)
        self.recordWords(identifyingWords, command)

        self.add_item(self.entityByDomain, domain, entity.entity_id)
        self.add_item(self.sentenceByDomain, command, domain + "." + service)
        self.add_item(self.entityNames, entity.entity_id, entityName)

        
        # TODO: Deal with properties
        #for field, field_properties in fields:
        #    if field_properties.get("required", False):
        #       self.recordWords(identifyingWords, ">" + field + "<")

        entityDescription = ""
        for word in identifyingWords:
            entityDescription += word + " "


        _LOGGER.debug(entityDescription)
        
        # TODO: Why is entityDescription a string rather than keep as a set?
        pair = [ entityDescription, service, entity.entity_id ]
        self.word_service.append(pair)
        identifyingWords.clear()


    def buildFromEntity(self, entity, entityName, domain, service, command, fields):
		# TODO: i18n
        initial = set(domain.split("_"))

        #TODO: Reinsate! 
        #self.recordService(initial, entity, service, command, fields )

        self.logForExperiment(initial, entity, entityName, domain, service, command, fields )


    async def adumpJson(self, outputpath):
        async with aiofiles.open(outputpath + '/entity-by-domain.json', 'w', encoding='utf-8') as file:
           await file.write(json.dumps(self.entityByDomain, ensure_ascii=False, default=list, indent=4))

        async with aiofiles.open(outputpath + '/sentences.json', 'w', encoding='utf-8') as file:
           await file.write(json.dumps(self.sentenceByDomain, ensure_ascii=False, default=list, indent=4))

        async with aiofiles.open(outputpath + '/entity-names.json', 'w', encoding='utf-8') as file:
           await file.write(json.dumps(self.entityNames, ensure_ascii=False, default=list, indent=4))

        _LOGGER.debug("Dumping json - done")


    async def adump1(self):
        _LOGGER.debug("Inside adump1")
        await self.adumpJson()

    def dumpJson(self):
        _LOGGER.debug("Inside Dumping json")
        self.adump1()


