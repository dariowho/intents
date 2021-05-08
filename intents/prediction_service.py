from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass

from intents import Intent
from intents.model.intent import IntentParameterMetadata
from intents.model.entity import SystemEntityMixin, _EntityMetaclass

class EntityMapping(ABC):
    """
    An Entity Mapping is a (de-)serializer for predicted Entities.

    Most of the times a Mapping is not needed as the Entity can be mapped
    directly to its type (e.g. "3" -> `Number(3)`). However, prediction services
    such as Dialogflow may define system entities of structured types; a notable
    example is Dialogflow's *sys.person* entity, which is returned as `{"name":
    "John"}` and thus needs to be mapped to `Person("John")`.

    Another notable scenario is Date/Time objects. A mapping can be used to
    convert time strings from the Service format to python objects.
    """

    @property
    @abstractmethod
    def entity_cls(self) -> _EntityMetaclass:
        """
        This is the internal entity type that is being mapped.

        >>> mapping = StringEntityMapping(Sys.Any, 'sys.any')
        >>> mapping.entity_cls
        Sys.Any
        """

    @property
    @abstractmethod
    def service_name(self) -> str:
        """
        This is the name of the Entity in the Prediction Service domain.

        >>> mapping = StringEntityMapping(Sys.Any, 'sys.any')
        >>> mapping.service_name
        'sys.any'
        """

    @abstractmethod
    def from_service(self, service_data: Any) -> SystemEntityMixin:
        """
        Converts the Service representation of an Entity (typically the value
        that is returned at prediction time) to an instance of one of the internal Entity
        classes in :class:`intents.model.entities`
        """

    @abstractmethod
    def to_service(self, entity: SystemEntityMixin) -> Any:
        """
        Converts a System Entity instance into a Service representation (typically,
        to be sent as a parameter of a trigger request)

        TODO: this is currently not used (string values are passed straight to
        prediction services).
        """

class StringEntityMapping(EntityMapping):

    entity_cls: _EntityMetaclass = None
    service_name: str = None

    def __init__(self, entity_cls: _EntityMetaclass, service_name: str):
        """
        :param service_name: name of the Entity in the Prediction Service
        """
        self.entity_cls = entity_cls
        self.service_name = service_name

    def from_service(self, service_data: Any) -> SystemEntityMixin:
        return self.entity_cls(service_data)

    def to_service(self, entity: SystemEntityMixin) -> Any:
        return str(entity)

class ServiceEntityMappings(dict):
    """
    Models a list of entity mappings. In addition to a standard list, two things
    are added:

    * Dict-like access to retrieve a mapping given its internal type (e.g.
      `mappings[Sys.Any]`)
    * Consistency check: a mapping list must cover all the entities defined in
      the framework (TODO)
    * Shortcut to define StringEntityMappings like `(Sys.Any, 'sys.any')` (TODO)
    """

    @classmethod
    def from_list(cls, mapping_list: List[EntityMapping]) -> "ServiceEntityMappings":
        result = cls()
        for mapping in mapping_list:
            if mapping in result:
                raise ValueError(f"Mapping {mapping} already defined in list: {mapping_list}")
            result[mapping.entity_cls] = mapping
        return result

@dataclass
class Prediction(ABC):
    """
    This class is meant to abstract prediction results from a generic Prediction
    Service. It uses names from Dialogflow, as it is currently the only
    supported service
    """
    intent_name: str
    confidence: str
    contexts: dict
    parameters_dict: dict
    fulfillment_messages: dict
    fulfillment_text: str = None

    @property
    @abstractmethod
    def entity_mappings(self) -> ServiceEntityMappings:
        """
        A Prediction subclass must know the Entity Mappings of its Prediction
        Service. :meth:`parameters` will use such mappings to convert parameters
        in `parameters_dict` to their generic `Sys.*` type.
        """

    def parameters(self, schema: Dict[str, IntentParameterMetadata]) -> Dict[str, Any]:
        """
        Cast parameters in `Prediction.parameters_dict` according to the given
        schema. This is necessary, because parameter types are not known at
        prediction time, and therefore they need to be determined by the
        corresponding :class:`Intent` class.
        """
        result = {}
        for param_name, param_value in self.parameters_dict.items():
            if param_name not in schema:
                raise ValueError(f"Found parameter {param_name} in Service Prediction, but Intent class does not define it.")
            param_metadata = schema[param_name]
            mapping = self.entity_mappings[param_metadata.entity_cls]
            if param_metadata.is_list:
                if not isinstance(param_value, list):
                    raise ValueError(f"Parameter {param_name} is defined as List, but returned value is not of 'list' type: {param_value}")
                result[param_name] = [mapping.from_service(x) for x in param_value]
            else:
                result[param_name] = mapping.from_service(param_value)
        return result

class PredictionService(ABC):
    """
    This is the interface that Prediction Services must implement to integrate
    with Agents.
    """

    # TODO: use a metaclass to validate this: must be a dict; all Sys entities
    # must be set as keys. Values must be either strings or EntityMapping object
    entity_mappings = None

    _agent: 'intents.Agent'

    @abstractmethod
    def predict_intent(self, message: str) -> Prediction:
        """
        Predict the Intent from the given User message

        :param message: The message to be classified
        """

    @abstractmethod
    def trigger_intent(self, intent: Intent) -> Prediction:
        """
        Trigger the given Intent and return the Service Prediction.
        """
