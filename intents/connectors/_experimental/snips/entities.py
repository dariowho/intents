import logging
import datetime
from enum import Enum
from intents import Sys, Entity
from intents.service_connector import EntityMapping, StringEntityMapping, ServiceEntityMappings

logger = logging.getLogger(__name__)

class BuiltinEntityTypes(Enum):
    MusicArtist = "snips/musicArtist"
    Number = "snips/number"

ENTITY_MAPPINGS = ServiceEntityMappings.from_list([
    StringEntityMapping(Entity, None),
    # StringEntityMapping(Sys.Person, SystemSlotTypes.Person.value),
    # StringEntityMapping(Sys.Color, SystemSlotTypes.Color.value),
    # DateMapping(),
    # DummyMapping(Sys.Email), # TODO: implement
    StringEntityMapping(Sys.Integer, BuiltinEntityTypes.Number.value),
    # StringEntityMapping(Sys.PhoneNumber, SystemSlotTypes.PhoneNumber.value),
    # StringEntityMapping(Sys.Language, SystemSlotTypes.Language.value),
    # DummyMapping(Sys.Url), # TODO: implement
    StringEntityMapping(Sys.MusicArtist, BuiltinEntityTypes.MusicArtist.value),
    # StringEntityMapping(Sys.MusicGenre, SystemSlotTypes.Genre.value)
])
