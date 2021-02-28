from typing import Any
from dataclasses import dataclass

class _EntityMetaclass(type):

    @property
    def metadata(cls):
        name = cls.__dict__.get('__df_name__')
        if not name:
            name = cls.__name__
        
        meta = cls.__dict__.get('meta')
        if not meta:
            meta = Entity.Meta()
        
        return Entity._Metadata(
            name=name,
            regex_entity = meta.regex_entity,
            automated_expansion = meta.automated_expansion,
            fuzzy_matching = meta.fuzzy_matching
        )

class EntityMixin(metaclass=_EntityMetaclass):
    """
    This is a mixin class for entities, that adds :meth:`from_df_response`, to
    build the Entity object from the match data in Dialogflow Responses.
    """

    @classmethod
    def from_df_response(cls, match: Any):
        """
        Buid the Entity object from the match data from a Dialogflow Response.
        Specifically, :var:`match` is the :class:`dict` version of
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
            
    @dataclass
    class _Metadata(Meta):
        """
        This class is used internally, to combine user-controlled parameters in
        :class:`Meta` with framework-controlled parameter `name`
        """
        name: str = None

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
        __df_name__ = "sys.any"

    class Integer(int, SystemEntityMixin):
        """
        Matches integers only
        """
        __df_name__ = "sys.number-integer"

    @dataclass
    class Person(SystemEntityMixin):
        """
        Matches common given names, last names or their combinations.
        """
        __df_name__ = "sys.person"

        name: str

    @dataclass
    class UnitCurrency(SystemEntityMixin):
        """
        Number + currency name
        """
        __df_name__ = "sys.unit-currency"

        amount: float
        currency: str
