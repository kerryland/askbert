
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


    def buildFromEntity(self, entity, entity_entry, domain, service, command, fields):
		# TODO: i18n
        initial = set(entity.domain.split("_"))

        self.recordService(initial, entity, service, command, fields )



