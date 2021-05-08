from typing import Any
from dataclasses import dataclass

class _EntityMetaclass(type):

    @property
    def name(cls):
        return cls.__name__

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

    @dataclass
    class Meta:
        """
        This class is used to set user-controlled Entity parameters
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

    class Any(str, SystemEntityMixin):
        """
        Matches any non-empty input
        """

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
