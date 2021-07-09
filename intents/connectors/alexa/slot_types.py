from enum import Enum
from intents import Sys
from intents.service_connector import EntityMapping, StringEntityMapping, ServiceEntityMappings

class SystemSlotTypes(Enum):
    Color = "AMAZON.Color"
    Genre = "AMAZON.Genre"
    Musician = "AMAZON.Musician"
    Number = "AMAZON.NUMBER"
    Language = "AMAZON.Language"
    Person = "AMAZON.Person"
    PhoneNumber = "AMAZON.PhoneNumber"

class DummyMapping(EntityMapping):
    service_name = "NOT_IMPLEMENTED"
    entity_cls = None

    def __init__(self, entity_cls):
        self.entity_cls = entity_cls
    def from_service(self, service_data):
        raise NotImplementedError()
    def to_service(self, entity):
        raise NotImplementedError()

ENTITY_MAPPINGS = ServiceEntityMappings.from_list([
    StringEntityMapping(Sys.Person, SystemSlotTypes.Person.value),
    StringEntityMapping(Sys.Color, SystemSlotTypes.Color.value),
    DummyMapping(Sys.Date), # TODO: implement
    DummyMapping(Sys.Email), # TODO: implement
    StringEntityMapping(Sys.Integer, SystemSlotTypes.Number.value),
    StringEntityMapping(Sys.PhoneNumber, SystemSlotTypes.PhoneNumber.value),
    StringEntityMapping(Sys.Language, SystemSlotTypes.Language.value),
    DummyMapping(Sys.Url), # TODO: implement
    StringEntityMapping(Sys.MusicArtist, SystemSlotTypes.Musician.value),
    StringEntityMapping(Sys.MusicGenre, SystemSlotTypes.Genre.value)
])