
import logging
import json

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


    def recordService(self, entity, service, identifyingWords):
        self.recordWords(identifyingWords, entity.attributes.get("friendly_name", None))
        self.recordWords(identifyingWords, entity.name)
        
		# TODO: i18n
        identifyingWords.add(entity.domain.split("_")
        
        entityDescription = ""
        for word in identifyingWords:
            entityDescription += word + " "

        _LOGGER.debug(entityDescription)
        
        pair = [ entityDescription, service, entity.entity_id ]
        self.word_service.append(pair)
        identifyingWords.clear()


    def buildFromEntity(self, entity, entity_entry, domain, service):
        friendly = entity.attributes.get("friendly_name")
        platform = entity_entry.platform

        _LOGGER.info(f"Building {friendly}:  {entity.entity_id} {domain} {service} {platform}")

        self.recordService(entity, service, set())



