
import logging

_LOGGER = logging.getLogger(__name__)

class SentenceBuilder() :

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
        identifyingWords.add(entity.domain)
        
        sentence = ""
        for word in identifyingWords:
            sentence += word + " "
        
        pair = [ sentence, service, entity.entity_id ]
        self.word_service.append(pair)
        _LOGGER.debug(sentence)
        identifyingWords.clear()



    def buildFromEntity(self, entity, domain, service):
        friendly = entity.attributes.get("friendly_name")
        _LOGGER.info(f"Building {friendly}:  {entity.entity_id} {domain} {service}")

        #entity_domain = entity.entity_id.split(".")[0]
        #entity_identifier  = entity.entity_id.split(".")[1]

        self.recordService(entity, service, set(domain.split("_")))



