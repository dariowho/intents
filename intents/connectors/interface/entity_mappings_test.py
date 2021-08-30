from typing import Any

import pytest

from intents import Sys, LanguageCode, Entity
from intents.model.entity import SystemEntityMixin
from intents.resources.builtin_entities.color import I_IntentsColor
from intents.connectors.interface import entity_mappings

def test_string_entity_mapping():
    mapping = entity_mappings.StringEntityMapping(Sys.Integer, "@FakeInteger")
    assert mapping.entity_cls == Sys.Integer
    assert mapping.service_name == "@FakeInteger"
    assert mapping.from_service("42") == Sys.Integer("42")
    assert mapping.to_service(42) == "42"

def test_patched_entity_mapping():
    mapping = entity_mappings.PatchedEntityMapping(Sys.Color, I_IntentsColor)
    assert mapping.entity_cls == Sys.Color
    assert mapping.service_name == "I_IntentsColor"
    assert mapping.from_service("red") == Sys.Color("red")
    assert mapping.to_service(Sys.Color("red")) == "red"

#
# ServiceEntityMappings
#

class MockCustomMapping(entity_mappings.EntityMapping):
    entity_cls = Sys.Person
    service_name = "@FakePerson"
    supported_languages = [LanguageCode.ENGLISH]
    def from_service(self, service_data: Any) -> SystemEntityMixin:
        return Sys.Person(service_data["name"])
    def to_service(self, entity: SystemEntityMixin) -> Any:
        return str({"name": entity})

MOCK_MAPPINGS = entity_mappings.ServiceEntityMappings.from_list([
    entity_mappings.StringEntityMapping(Sys.PhoneNumber, "@FakePhoneNumber"),
    MockCustomMapping()
])

def test_mappings__sys_found():
    mapping = MOCK_MAPPINGS.lookup(Sys.PhoneNumber)
    assert mapping == entity_mappings.StringEntityMapping(Sys.PhoneNumber, "@FakePhoneNumber")
    
    assert MOCK_MAPPINGS.service_name(Sys.PhoneNumber) == "@FakePhoneNumber"
    assert MOCK_MAPPINGS.is_mapped(Sys.PhoneNumber, LanguageCode.ENGLISH)
    assert MOCK_MAPPINGS.is_mapped(Sys.PhoneNumber, LanguageCode.SPANISH_LATIN_AMERICA)

def test_mappings__supported_languages():
    mapping = MOCK_MAPPINGS.lookup(Sys.Person)
    assert isinstance(mapping, MockCustomMapping)
    
    assert MOCK_MAPPINGS.service_name(Sys.Person) == "@FakePerson"
    assert MOCK_MAPPINGS.is_mapped(Sys.Person, LanguageCode.ENGLISH)
    assert not MOCK_MAPPINGS.is_mapped(Sys.Person, LanguageCode.SPANISH_LATIN_AMERICA)

def test_mappings__sys_not_found():
    with pytest.raises(KeyError):
        MOCK_MAPPINGS.lookup(Sys.Color)

    assert not MOCK_MAPPINGS.is_mapped(Sys.Color, LanguageCode.ENGLISH)

def test_mappings__custom_entity():
    class MyCustomEntity(Entity):
        pass

    mapping = MOCK_MAPPINGS.lookup(MyCustomEntity)
    assert mapping == entity_mappings.StringEntityMapping(
        entity_cls=MyCustomEntity,
        service_name="MyCustomEntity"
    )
    assert MOCK_MAPPINGS.service_name(MyCustomEntity) == "MyCustomEntity"
