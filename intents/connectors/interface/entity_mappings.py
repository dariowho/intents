"""
Entity Mappings are used to (de-)serialize entity types and values in the
communication between a
:class:`~intents.connectors.interface.connector.Connector` and its Service. This
is done when

* Connector exports Agent to Service; here system entity names (e.g.
  :class:`Sys.Integer`) must be converted to Service name (e.g.
  `@sys.number-integer` in Dialogflow)
* Connector processes a Prediction or Fulfillment payload; in this case, not
  only a reverse lookup is needed, but it may be necessary to de-serialize an
  entity value as well. For innstance, ISO datetime strings mut be cast to
  Python datetime objects
* Connector triggers an Intent on Service; here parameter names must be
  converted, and values must be serialized

The base class for mappings is :class:`EntityMapping`. Two builtin convenience
mappings are also available: :class:`StringEntityMapping`,
and :class:`PatchedEntityMapping`.

It is convenient to collect Connector mappings in a
:class:`ServiceEntityMapping` dict, which implements some utility methods
related to mapping collections.

Finally, here we also define :func:`deserialize_intent_parameters`, a helper
that turns a dict of parameters in the Service format and converts it into a
dict of *Intents* entities.
"""

import logging
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any, List, Dict, Type

from intents import Intent, Entity, LanguageCode
from intents.model.entity import EntityMixin, SystemEntityMixin

logger = logging.getLogger(__name__)

# TODO: turn it to an abstract class, when pylint will support dataclass
# implementation of abstract properties
class EntityMapping():
    """
    An Entity Mapping is a (de-)serializer for predicted Entities.

    Most of the times a Mapping is not needed as the Entity can be mapped
    directly to its type (e.g. "3" -> `Number(3)`). However, prediction services
    such as Dialogflow may define system entities of structured types; a notable
    example is Dialogflow's *sys.person* entity, which is returned as `{"name":
    "John"}` and therefore needs custom logic to be mapped to `Person("John")`.
    This is modelled in :class:`intents.connectors.dialogflow_es.entities.PersonEntityMapping`.

    Another notable scenario is Date/Time objects. A mapping can be used to
    convert time strings from the Service format to python objects. For
    Dialogflow ES, this is modelled in  :class:`intents.connectors.dialogflow_es.entities.DateTimeEntityMapping`.
    """

    @property
    def entity_cls(self) -> Type[EntityMixin]:
        """
        This is the internal entity type that is being mapped.

        >>> mapping = StringEntityMapping(Sys.Integer, 'sys.number-integer')
        >>> mapping.entity_cls
        Sys.Integer
        """
        raise NotImplementedError()

    @property
    def service_name(self) -> str:
        """
        This is the name of the Entity in the Prediction Service domain.

        >>> mapping = StringEntityMapping(Sys.Integer, 'sys.number-integer')
        >>> mapping.service_name
        'sys.number-integer'
        """
        raise NotImplementedError()

    @property
    def supported_languages(self) -> List[LanguageCode]:
        """
        It may happen that a Prediction Service only supports an Entity for a
        limited set of languages. For instance, Snips NLU only supports its
        `snips/date` entity in English.

        This property is set to `None` when the mapping is valid for all the
        service-supported language. If support is restricted to a subset of
        them, it will contain the list of language codes. Export and prediction
        procedures must handle accordingly.
        """
        return None

    @abstractmethod
    def from_service(self, service_data: Any) -> SystemEntityMixin:
        """
        De-serialize the Service representation of an Entity (typically the value
        that is returned at prediction time) to an instance of one of the internal Entity
        classes in :class:`intents.model.entities`

        >>> date_mapping.from_service("2021-07-11")
        Sys.Date(2021, 7, 11)

        :param service_data: A parameter value, as it is returned by the Service
                             in a prediction/trigger response
        :return: the parameter value, modelled as one of the System Entity classes
        """

    @abstractmethod
    def to_service(self, entity: SystemEntityMixin) -> Any:
        """
        Serialize a System Entity instance into a Service representation (typically,
        to be sent as a parameter of a trigger request)

        >>> date_mapping.to_service(Sys.Date(2021, 7, 11))
        "2021-07-11"

        Args:
            entity: The System Entity to serialize

        Returns:
            The serialized Entity that can be sent to Service (e.g. in a trigger request)
        """

@dataclass(frozen=True)
class StringEntityMapping(EntityMapping):
    """
    This is a generic :class:`EntityMapping` that reads values as they are sent
    by the prediction service (e.g. `"3"` -> `Sys.Integer("3")`), and serializes
    by simple string conversion (e.g. `Sys.Integer(3)` -> "3"). This is the most
    common case when dealing with entities.

    The System Entity to use must be defined when instantiating the mapping, for
    instance:

    >>> StringEntityMapping(Sys.Integer, "sys.number-integer")

    Args:
        entity_cls: One of the `Sys.*` entity classes
        service_name: Name of the corresponding entity within the Prediction
            Service
    """

    entity_cls: Type[EntityMixin] = None
    service_name: str = None

    def from_service(self, service_data: Any) -> SystemEntityMixin:
        return self.entity_cls(service_data)

    def to_service(self, entity: SystemEntityMixin) -> Any:
        return str(entity)

@dataclass(frozen=True)
class PatchedEntityMapping(EntityMapping):
    """
    Different Prediction Services support different entities. For instance,
    :class:`Sys.Color` is native in Dialogflow, but is not supported in Snips.
    In some cases, we can patch missing system entities with custom ones; for
    instance, :class:`Sys.Color` can be patched with builtin
    :class:`~intents.resources.builtin_entities.color.I_IntentsColor`.
    `PatchedEntityMapping` can be use to define mappings for system entities
    that are patched with custom ones.

    Connectors that use patched entities must define logic to handle
    `PatchedEntityMapping` in their export procedures.

    By default, `builtin_entity.name` is used as Service entity name, and values
    are (de)serialized as simple strings. If a Connector have different
    required, it should define a custom subclass of `PatchedEntityMapping`.
    """
    entity_cls: Type[EntityMixin] = None
    builtin_entity: Entity = None

    @property
    def service_name(self):
        return self.builtin_entity.name

    def from_service(self, service_data: Any) -> SystemEntityMixin:
        return self.entity_cls(service_data)

    def to_service(self, entity: SystemEntityMixin) -> Any:
        return str(entity)

class ServiceEntityMappings(dict):
    """
    Models a collection of entity mappings, in the form of a dict where the key is a
    System entity class (i.e. inherits from :class:`SystemEntityMixin`) and the value
    is a :class:`EntityMapping`. In addition to a standard dict, these features
    are added:

    * Instantiate from a list of mappings with :meth:`from_list`
    * Flexible lookup with :meth:`ServiceEntityMapping.lookup`
    """

    def lookup(self, entity_cls: Type[EntityMixin]) -> EntityMapping:
        """
        Return the mapping in the dictionary that is associated with the given
        `entity_cls`. In addition to a simple `mappings[entity_cls]`, this
        method also implements a fallback for Custom Entities. That is, when a
        Custom Entity is not in the mapping dict (typically they are not),
        retrieve return an on-the-fly mapping generated with
        :meth:`~ServiceEntityMappings.custom_entity_mapping`.

        Args:
            entity_cls: The Entity class to lookup
        Returns:
            The mapping that refers to the given Entity class
        Raises:
            KeyError: If no mapping exists that can be used for `entity_cls`
        """
        # `Entity` objects are custom entities
        if issubclass(entity_cls, Entity) and entity_cls not in self:
            return self.custom_entity_mapping(entity_cls)
        if entity_cls not in self:
            mapped_entities = [m.entity_cls for m in self.values()]
            raise KeyError(f"Failed to lookup entity {entity_cls} in mappings. Mapped entities: {mapped_entities}")
        return self[entity_cls]

    def custom_entity_mapping(self, entity_cls: Type[EntityMixin]) -> EntityMapping:
        """
        Generate an entity mapping on the fly for the given custom entity. This
        is needed because, while System entities are static, Custom ones need to
        be handled dynamically at run time.

        By default, this returns a simple :class:`StringEntityMapping`, where
        `service_name` is `entity_cls.name`. Connectors may override this method
        to implement custom behavior.

        Args:
            entity_cls: A Custom Entity for which a mapping will be generated

        Returns:
            A mapping for the given Entity
        """
        return StringEntityMapping(
            entity_cls=entity_cls,
            service_name=entity_cls.name
        )

    def service_name(self, entity_cls: Type[EntityMixin]):
        """
        Return the name of the given entity in the specific service; this can be
        the class name itself, or an :class:`EntityMapping` lookup in the case
        of System Entities.

        For instance, a :class:`Sys.Person` Entity will need to be looked up in
        the mappings to find out its service name (`sys.person` in Dialogflow,
        `AMAZON.Person` in Alexa, and so on). A custom entity (e.g. `PizzaType`)
        will use its class name instead.
        """
        return self.lookup(entity_cls).service_name

    def is_mapped(self, entity_cls: Type[EntityMixin], lang: LanguageCode) -> bool:
        """
        Return `False` if no mapping is defined for the given entity. Also
        return `False` if a mapping exists, but the mapping defines
        :attr:`~EntityMapping.supported_languages` and the given language is not
        in the list.

        Args:
            entity_cls: The Entity class to lookup
            lang: The language that should be supported by the mapping
        """
        try:
            mapping = self.lookup(entity_cls)
        except KeyError:
            return False

        if not mapping.supported_languages:
            return True

        return lang in mapping.supported_languages

    @classmethod
    def from_list(cls, mapping_list: List[EntityMapping]) -> "ServiceEntityMappings":
        """
        Convenience method for building a mapping from a list, instead of
        specifying the whole dict. See Dialogflow's
        :mod:`~intents.connectors.dialogflow_es.entities` module for an example.

        Args:
            mapping_list: The mappings that will be used to build the
                `ServiceEntityMapping` dict
        Returns:
            A `ServiceEntityMapping` with the given mappings
        """
        result = cls()
        for mapping in mapping_list:
            if mapping in result:
                raise ValueError(f"Mapping {mapping} already defined in list: {mapping_list}")
            result[mapping.entity_cls] = mapping
        return result

def deserialize_intent_parameters(
    service_parameters: Dict[str, Any],
    intent_cls: Type[Intent],
    mappings: ServiceEntityMappings
) -> Dict[str, EntityMixin]:
    """
    Cast parameters from Service format to Intents format according to the given
    schema. Typically this happens when a Connector has to turn prediction
    parameters into *Intents* entities.

    Args:
        service_parameters: The parameters dict, as it is returned by a Prediction Service
        intent_cls: The Intent parameters will be matched against
        mappings: The Service Entity Mappings, to deserialize parameter values
    Return:
        A dictionary like `service_parameters`, but all the values are converted
        to native Intents Entity objects.
    """
    result = {}
    schema = intent_cls.parameter_schema
    for param_name, param_value in service_parameters.items():
        if param_name not in schema:
            raise ValueError(f"Found parameter {param_name} in Service Prediction, but Intent "
                             "class does not define it. Make sure your cloud Agent is in sync "
                             "with your local one. A new upload() may solve the issue")
        param_metadata = schema[param_name]
        entity_cls = param_metadata.entity_cls
        mapping = mappings.lookup(entity_cls)
        try:
            if param_metadata.is_list:
                if not isinstance(param_value, list):
                    raise ValueError(f"Parameter {param_name} is defined as List, but returned value is not of 'list' type: {param_value}")
                result[param_name] = [mapping.from_service(x) for x in param_value]
            else:
                result[param_name] = mapping.from_service(param_value)
        except Exception as exc:
            raise RuntimeError(f"Failed to match parameter '{param_name}' with value '{param_value}' against schema {schema}. See source exception above for details.") from exc

    return result
