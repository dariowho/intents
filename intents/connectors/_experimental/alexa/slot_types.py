import logging
import datetime
from enum import Enum
from intents import Sys
from intents.connectors.interface import EntityMapping, StringEntityMapping, ServiceEntityMappings
from intents.connectors._experimental.alexa.dates import parse_alexa_date

logger = logging.getLogger(__name__)

class SystemSlotTypes(Enum):
    Color = "AMAZON.Color"
    Genre = "AMAZON.Genre"
    Musician = "AMAZON.Musician"
    Number = "AMAZON.NUMBER"
    Language = "AMAZON.Language"
    Person = "AMAZON.Person"
    PhoneNumber = "AMAZON.PhoneNumber"

class DummyMapping(EntityMapping):
    service_name = None
    entity_cls = None

    def __init__(self, entity_cls, service_name="NOT_IMPLEMENTED"):
        self.entity_cls = entity_cls
        self.service_name = service_name
    def from_service(self, service_data):
        raise NotImplementedError(f"This Connector uses a Dummy Mapping for entity {self.entity_cls}.")
    def to_service(self, entity):
        raise NotImplementedError(f"This Connector uses a Dummy Mapping for entity {self.entity_cls}.")

class DateMapping(EntityMapping):
    entity_cls = Sys.Date
    service_name = "AMAZON.DATE"
    
    def from_service(self, service_data: str) ->  Sys.Date:
        if not isinstance(service_data, str):
            raise ValueError("Found non-string value for AMAZON.DATE entity. This is possibly a bug, please file an issue at https://github.com/dariowho/intents")

        date_from, date_to = parse_alexa_date(service_data)
        if date_to:
            # TODO: There could be an Alexa-only entity that maps to date intervals
            logger.warning("Alexa slot of type AMAZON.DATE contains an interval (e.g. 'this weekend', 'next winter'...). This case is not handled yet: the first day of the interval will be returned")

        return Sys.Date.from_py_date(date_from)

    def to_service(self, entity: datetime.date) -> str:
        return str(entity)

ENTITY_MAPPINGS = ServiceEntityMappings.from_list([
    StringEntityMapping(Sys.Person, SystemSlotTypes.Person.value),
    StringEntityMapping(Sys.Color, SystemSlotTypes.Color.value),
    DateMapping(),
    DummyMapping(Sys.Email), # TODO: implement
    StringEntityMapping(Sys.Integer, SystemSlotTypes.Number.value),
    StringEntityMapping(Sys.PhoneNumber, SystemSlotTypes.PhoneNumber.value),
    StringEntityMapping(Sys.Language, SystemSlotTypes.Language.value),
    DummyMapping(Sys.Url), # TODO: implement
    StringEntityMapping(Sys.MusicArtist, SystemSlotTypes.Musician.value),
    StringEntityMapping(Sys.MusicGenre, SystemSlotTypes.Genre.value)
])