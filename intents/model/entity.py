"""
Entities are special chunks of text in the User utterances, that are recognized
and extratcted as parameters during predictions. For instance, in an utterance like
*"My name is John"* we most likely want to match *"John"* as a Person Entity.

Two types of Entities exist:

* **System entities** are built-in types that most chatbot frameworks will
  recognize (names, cities, numbers, emails, ...). These are modelled in
  :class:`Sys`.
* **Custom entities** are user-defined entity types, that typically consist in a
  list of possible values and their synonims. For instance, a `PizzaType` custom entity
  will have values like *"margherita"*, *"marinara"*, *"diavola"* and so on, and each
  of these may define some synonims; this way, in an utterance like *"I want a
  pepperoni pizza"*, the *"pepperoni"* chunk can be recognized as a `PizzaType`
  parameter, and mapped to its correct name, which is *"diavola"*. Custom entities
  are defined by extending the :class:`Entity` base class.
"""
import datetime
from typing import Any, List, Dict
from dataclasses import dataclass

class _EntityMetaclass(type):

    name: str = None
    custom_language_data: Dict["language.LanguageCode", List["language.EntityEntry"]] = None

    def __new__(cls, name, bases, dct):
        result_cls = super().__new__(cls, name, bases, dct)

        # Do not process Intent base class
        if name in ['Entity', 'EntityMixin', 'SystemEntityMixin']:
            # TODO: check if user isn't defining "class Entity(intents.Entity)" for
            # some reason
            return result_cls

        if not result_cls.name:
            result_cls.name = result_cls.__name__

        return result_cls

    @property
    def metadata(cls) -> "Entity.Meta":
        """
        TODO: consider removing this altogether, a `metadata` field in Entity
        may be enough
        """
        meta = cls.__dict__.get('meta')
        if not meta:
            return Entity.Meta()

        return meta

class EntityMixin(metaclass=_EntityMetaclass):
    """
    This is a mixin class for entities, that adds :meth:`from_df_response`, to
    build the Entity object from the match data in Dialogflow Responses.
    """

    @classmethod
    def from_df_response(cls, match: Any):
        """
        Buid the Entity object from the match data from a Dialogflow Response.
        Specifically, `match` is the :class:`dict` version of
        `queryResult.parameters.<PARAMETER_NAME>`.
        """
        if isinstance(match, dict):
            return cls(**match)

        return cls(match)

class Entity(str, EntityMixin):
    """
    Custom Entities are defined by users to match parameters that are specific
    to the Agent's domain. This is done by extending this class:

    .. code-block:: python

        from dataclasses import dataclass
        from intents import Intent, Entity

        class PizzaType(Entity):
            \"\"\"One of the pizza types that a Customer can order\"\"\" 

        @dataclass
        class customer_orders_pizza(Intent):
            \"\"\"A little docstring for my Intent\"\"\"

            pizza_type: PizzaType

    Language resources are expected for the `PizzaType` Entity. Like Intents,
    these will be looked up from the folder where the :class:`Agent` main class
    is defined, and specifically in
    `language/<LANGUAGE-CODE>/ENTITY_PizzaType.yaml`. More details in
    :mod:`intents.language`.
    """

    name: str = None

    @dataclass
    class Meta:
        """
        This class is used to set user-controlled Entity parameters.

        **NOTE**: usage of Meta is experimental, it may be removed in upcoming
        releases. 
        """
        regex_entity: bool = False
        automated_expansion: bool = False
        fuzzy_matching: bool = False

    meta: Meta = None

class SystemEntityMixin(EntityMixin):
    """
    This is used to signal that the entity is one of the Dialogflow default
    entities and doesn't need language resources.
    """

class Sys:
    """
    This is a container class, that defines all the system entities that are
    supported in the *Intents* framework. You can use system entities just like
    this:
    
    .. code-block:: python

        from dataclasses import dataclass
        from intents import Intent, Sys

        @dataclass
        class user_says_name(Intent):
            \"\"\"A little docstring for my Intent\"\"\"

            user_name: Sys.Person

    **NOTE**: This class is still work in progress.
    """

    # class Any(str, SystemEntityMixin):
    #     """
    #     Matches any non-empty input
    #
    #     NOTE: Sys.Any is tricky: not all prediction services support it, and
    #     the ones that do (including Dialoglfow) often misbehave when using it.
    #     """

    class Date(datetime.date, SystemEntityMixin):
        """
        Matches a date as a Python :class:`datetime.date` object
        """

        @staticmethod
        def from_py_date(py_date: datetime.date):
            """
            Clone the given :class:`datetime.date` object into a `Sys.Date` object
            """
            return Sys.Date(py_date.year, py_date.month, py_date.day)

    class Time(datetime.time, SystemEntityMixin):
        """
        Matches a time reference as a Python :class:`datetime.time` object
        """

        @staticmethod
        def from_py_time(py_time: datetime.time):
            """
            Clone the given :class:`datetime.time` object into a `Sys.Time` object
            """
            return Sys.Time(py_time.hour, py_time.minute, py_time.second, tzinfo=py_time.tzinfo)

    class Integer(int, SystemEntityMixin):
        """
        Matches integers only
        """

    class Person(str, SystemEntityMixin):
        """
        Matches common given names, last names or their combinations.

        Note that in Dialogflow this is returned as an Object (e.g. `{"name":
        "John"}`), while here we define `Person` as a String. The Dialogflow
        module defines proper entity mappings to handle the conversion.
        """

    class MusicArtist(str, SystemEntityMixin):
        """
        Matches the name of a music artist
        """

    class MusicGenre(str, SystemEntityMixin):
        """
        Matches a music genre (rock, pop, reggae, ...)
        """

    # @dataclass
    # class UnitCurrency(SystemEntityMixin):
    #     """
    #     Number + currency name
    #     """
    #     __df_name__ = "sys.unit-currency"

    #     amount: float
    #     currency: str
