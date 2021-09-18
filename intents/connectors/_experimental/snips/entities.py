import logging
from enum import Enum
from typing import Union, Type
from datetime import datetime, date

from intents import Sys, Entity, EntityMixin
from intents.language import LanguageCode
from intents.resources.builtin_entities import color, language, music_genre, first_name
from intents.connectors.interface import EntityMapping, StringEntityMapping, PatchedEntityMapping, ServiceEntityMappings

logger = logging.getLogger(__name__)

class BuiltinEntityTypes(Enum):
    MusicArtist = "snips/musicArtist"
    Number = "snips/number"
    Date = "snips/date"

class SnipsStringEntityMapping(StringEntityMapping):
    """
    Entities are always predicted as dicts. Simple ones just have a "value"
    field inside.
    """
    def from_service(self, service_data: dict):
        return self.entity_cls(service_data["value"])

class SnipsPatchedEntityMapping(PatchedEntityMapping):
    """
    Entities are always predicted as dicts. Simple ones just have a "value"
    field inside.
    """
    def from_service(self, service_data: dict):
        return self.entity_cls(service_data["value"])

class PlaceholderEntityMapping(SnipsStringEntityMapping):
    """
    Some entities are not supported in Snips, but can be replaced by empty
    placeholder custom entities. Snips NLU will try to infer values based on
    example utterance data only.

    This class is only meant to signal the export procedure that when this
    mapping is needed, an empty entity should be created.
    """

# TODO: implement custom processing unit for Snips to support regex-based
# entities (url, email, phone number, ...)

class DateMapping(EntityMapping):
    """
    This is a sample prediction with a Date entity:

    .. code-block:: json

    {
        "input": "My birthday is in two weeks",
        "intent": {
            "intentName": "UserSaysBirthday",
            "probability": 1.0
        },
        "slots": [
            {
                "range": {
                    "start": 15,
                    "end": 27
                },
                "rawValue": "in two weeks",
                "value": {
                    "kind": "InstantTime",
                    "value": "2021-08-21 00:00:00 +02:00",
                    "grain": "Day",
                    "precision": "Exact"
                },
                "entity": "snips/date",
                "slotName": "birthday_date"
            }
        ]
    }

    The mapping will receive the content of `slots[0].value`
    """
    entity_cls = Sys.Date
    service_name = BuiltinEntityTypes.Date.value
    supported_languages = [LanguageCode.ENGLISH]

    def from_service(self, service_data: dict):
        if (kind := service_data.get("kind")) != 'InstantTime':
            logger.warning("Expected returned date to be of 'InstantTime' kind. Snips returned '%s' "
                           "instead. This may cause unpredictable behavior.", kind)

        if (grain := service_data.get("grain")) != 'Day':
            logger.warning("Expected returned date to be of 'Day' grain. Snips returned '%s' "
                           "instead. This may cause unpredictable behavior.", grain)

        dt = datetime.fromisoformat(service_data["value"])
        return Sys.Date.from_py_date(dt.date())

    def to_service(self, entity: Union[date, datetime, str]):
                                      # ^ Sys.Date is subclass of date
        if isinstance(entity, datetime):
            entity = entity.date()
        return str(entity)

class SnipsEntityMappings(ServiceEntityMappings):

    def custom_entity_mapping(self, entity_cls: Type[EntityMixin]):
        return SnipsStringEntityMapping(
            entity_cls=entity_cls,
            service_name=entity_cls.name
        )

ENTITY_MAPPINGS = SnipsEntityMappings.from_list([
    SnipsPatchedEntityMapping(Sys.Person, first_name.I_IntentsFirstName),
    SnipsPatchedEntityMapping(Sys.Color, color.I_IntentsColor),
    DateMapping(),
    PlaceholderEntityMapping(Sys.Email, "I_PlaceholderEmail"),
    SnipsStringEntityMapping(Sys.Integer, BuiltinEntityTypes.Number.value),
    PlaceholderEntityMapping(Sys.PhoneNumber, "I_PlaceholderPhoneNumber"),
    PatchedEntityMapping(Sys.Language, language.I_IntentsLanguage),
    PlaceholderEntityMapping(Sys.Url, "I_PlaceholderUrl"),
    SnipsStringEntityMapping(Sys.MusicArtist, BuiltinEntityTypes.MusicArtist.value),
    SnipsPatchedEntityMapping(Sys.MusicGenre, music_genre.I_IntentsMusicGenre),
])

BUILTIN_ENTITIES = [m.entity_cls for m in ENTITY_MAPPINGS.values() if m.service_name in [x.value for x in BuiltinEntityTypes]]
PATCHED_MAPPINGS = [m for m in ENTITY_MAPPINGS.values() if isinstance(m, PatchedEntityMapping)]
PLACEHOLDER_ENTITIES = [m.entity_cls for m in ENTITY_MAPPINGS.values() if isinstance(m, PlaceholderEntityMapping)]
