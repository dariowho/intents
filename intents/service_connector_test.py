import pytest

from intents import Sys, Agent, Entity
from intents.language import LanguageCode
from intents.connectors.interface import Connector, StringEntityMapping, ServiceEntityMappings

class DummyConnector(Connector):

    entity_mappings = ServiceEntityMappings.from_list([
        StringEntityMapping(Sys.Person, "fake-person-service-name")
    ])

    def predict(self, message, session, language):
        return None
    
    def trigger(self, intent, session, language):
        return None
    
    def fulfill(self, fulfillment_request):
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

def test_language_code_string_is_cast():
    connector = DummyConnector(DummyAgent, default_language="en")
    assert connector.default_language == LanguageCode.ENGLISH

    connector = DummyConnector(DummyAgent, default_language=LanguageCode.ENGLISH)
    assert connector.default_language == LanguageCode.ENGLISH

def test_first_language_is_default():
    connector = DummyConnector(DummyAgent)
    assert connector.default_language == LanguageCode.ITALIAN

def test_entity_mappings__system_entity():
    m = StringEntityMapping(Sys.Person, "fake-person-service-name")
    mappings = ServiceEntityMappings.from_list([m])

    assert mappings.lookup(Sys.Person) is m
    assert mappings.service_name(Sys.Person) == "fake-person-service-name"

def test_entity_mappings__custom_entity():
    mappings = ServiceEntityMappings()

    class MockCustomEntity(Entity):
        pass

    class MockCustomEntityWithName(Entity):
        name = "my_entity_name"

    assert mappings.lookup(MockCustomEntity) == StringEntityMapping(MockCustomEntity, "MockCustomEntity")
    assert mappings.lookup(MockCustomEntityWithName) == StringEntityMapping(MockCustomEntityWithName, "my_entity_name")

    assert mappings.service_name(MockCustomEntity) == "MockCustomEntity"
    assert mappings.service_name(MockCustomEntityWithName) == "my_entity_name"

def test_entity_mappings__key_error():
    m = StringEntityMapping(Sys.Person, "fake-person-service-name")
    mappings = ServiceEntityMappings.from_list([m])

    class MockCustomEntity(Entity):
        pass

    with pytest.raises(KeyError):
        mappings.lookup(Sys.PhoneNumber)

    with pytest.raises(KeyError):
        mappings.service_name(Sys.PhoneNumber)
