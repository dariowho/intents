from intents import Sys, Agent
from intents.language import LanguageCode
from intents.service_connector import Connector, StringEntityMapping, ServiceEntityMappings

class DummyConnector(Connector):

    entity_mappings = ServiceEntityMappings.from_list([
        StringEntityMapping(Sys.Person, "fake-person-service-name")
    ])

    def predict(self, message, session, language):
        return None
    
    def trigger(self, intent, session, language):
        return None
    
    def upload(self):
        return None

    def export(self, destination):
        return None

class DummyAgent(Agent):
    languages = ['it', 'en']

def test_default_session_is_not_none():
    connector = DummyConnector(DummyAgent)
    assert connector.default_session

def test_system_service_entity_name_lookup():
    connector = DummyConnector(DummyAgent)
    assert connector._entity_service_name(Sys.Person) == "fake-person-service-name"

def test_language_code_string_is_cast():
    connector = DummyConnector(DummyAgent, default_language="en")
    assert connector.default_language == LanguageCode.ENGLISH

    connector = DummyConnector(DummyAgent, default_language=LanguageCode.ENGLISH)
    assert connector.default_language == LanguageCode.ENGLISH

def test_first_language_is_default():
    connector = DummyConnector(DummyAgent)
    assert connector.default_language == LanguageCode.ITALIAN
