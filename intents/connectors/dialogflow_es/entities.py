import logging
import datetime

from intents.model.entity import Sys, Entity
from intents.connectors.interface import EntityMapping, StringEntityMapping, ServiceEntityMappings

class PersonEntityMapping(EntityMapping):
    """
    Dialogflow's `sys.person` entity type is returned as an object like
    `{"name": "Guido"}`
    """

    entity_cls = Sys.Person
    service_name = 'sys.person'

    def from_service(self, service_data: dict) -> Sys.Person:
        if isinstance(service_data, str):
            service_data = {"name": service_data}
        return Sys.Person(service_data['name'])

    def to_service(self, entity: Sys.Person) -> dict:
        return {"name": str(entity)}

class TimeEntityMapping(EntityMapping):
    """
    Dialogflow's `sys.time` entity is returned as a full ISO datetime string
    (e.g. "2021-06-19T13:00:00+02:00"). We only consider the time part, which is
    returned as a :class:`datetime.time` object. The timezone is the same as the
    one that is returned by Dialogflow.

    Both :class:`datetime.time` and :class:`str` can be serialized to be used as
    parameter values. As :class:`Sys.Time` inherits from :class:`datetime.time`,
    these are all valid usages:

    >>> connector.trigger(lunch_time(time=Sys.Time(12, 30)))
    >>> connector.trigger(lunch_time(time=datetime.time(12, 30)))
    >>> connector.trigger(lunch_time(time="12:30:00"))

    Note that strings will be sent to Dialogflow without checks: be sure to use
    valid time references. Also, note that Dialogflow won't resolve relative
    time references in triggers. The following code will result in an error:

    >>> connector.trigger(lunch_time(time="in 10 minutes"))
    RuntimeError: ...
    """

    entity_cls = Sys.Time
    service_name = 'sys.time'

    def from_service(self, service_data: str) -> Sys.Time:
        dt = datetime.datetime.fromisoformat(service_data)
        return Sys.Time.from_py_time(dt.timetz())

    def to_service(self, entity: Sys.Time) -> str:
        # TODO: check
        return str(entity)

class DateEntityMapping(EntityMapping):
    """
    Dialogflow's `sys.date` entity is returned as a full ISO datetime string
    (e.g. "2021-06-19T13:00:00+02:00"). We only consider the date part, which is
    returned as a :class:`datetime.date` object (specifically, :class:`Sys.Date`).

    Both :class:`datetime.date` and :class:`str` can be serialized to be used as
    parameter values. As :class:`Sys.Date` inherits from :class:`datetime.date`,
    these are all **valid** usages:

    >>> connector.trigger(birthday_intent(date=Sys.Date(2021, 07, 21)))
    >>> connector.trigger(birthday_intent(date=datetime.date(2021, 07, 21)))
    >>> connector.trigger(birthday_intent(date="2021-07-21"))

    Note that strings will be sent to Dialogflow without checks: be sure to use
    valid date references. Also, note that Dialogflow won't resolve relative
    date references in triggers. The following code will result in an **error**:

    >>> connector.trigger(birthday_intent(date="tomorrow"))
    RuntimeError: ...
    """

    entity_cls = Sys.Date
    service_name = 'sys.date'

    def from_service(self, service_data: str) -> Sys.Date:
        df_datetime = datetime.datetime.fromisoformat(service_data)
        return Sys.Date.from_py_date(df_datetime.date())

    def to_service(self, entity: datetime.date) -> str:
        return str(entity)


MAPPINGS = ServiceEntityMappings.from_list([
    # StringEntityMapping(Sys.Any, "sys.any"),
    DateEntityMapping(),
    TimeEntityMapping(),
    StringEntityMapping(Sys.Integer, "sys.number-integer"),
    StringEntityMapping(Sys.Email, "sys.email"),
    StringEntityMapping(Sys.PhoneNumber, "sys.phone-number"),
    StringEntityMapping(Sys.Color, "sys.color"),
    StringEntityMapping(Sys.Language, "sys.language"),
    StringEntityMapping(Sys.Url, "sys.url"),
    PersonEntityMapping(),
    StringEntityMapping(Sys.MusicArtist, "sys.music-artist"),
    StringEntityMapping(Sys.MusicGenre, "sys.music-genre"),
])
