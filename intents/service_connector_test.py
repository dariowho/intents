from intents import Sys
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

def test_default_session_is_not_none():
    connector = DummyConnector(None)
    assert connector.default_session

def test_system_service_entity_name_lookup():
    connector = DummyConnector(None)
    assert connector._entity_service_name(Sys.Person) == "fake-person-service-name"
