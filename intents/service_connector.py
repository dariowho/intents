"""
Connectors allow *Intents* Agent definitions to operate with real cloud services
such as Dialogflow, Lex or Azure Bot Services. Currently, only one connector is
provided with this library, and this is for Dialogflow ES:
:mod:`intents.connectors.dialogflow_es.connector`.

Connectors are used to operate with the cloud version of the Agent, and
specifically to:

* Export an :class:`intents.Agent` in a format that is natively readable by the
  Service
* Predict User messages on the Cloud Agent
* Trigger Intents on the Cloud Agent

More details can be found in the :class:`Connector` interface.
"""
from uuid import uuid1
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from dataclasses import dataclass

from intents import Intent, Agent
from intents.model.intent import IntentParameterMetadata
from intents.model.entity import SystemEntityMixin, _EntityMetaclass
from intents.language import IntentResponse, IntentResponseGroup

class EntityMapping(ABC):
    """
    An Entity Mapping is a (de-)serializer for predicted Entities.

    Most of the times a Mapping is not needed as the Entity can be mapped
    directly to its type (e.g. "3" -> `Number(3)`). However, prediction services
    such as Dialogflow may define system entities of structured types; a notable
    example is Dialogflow's *sys.person* entity, which is returned as `{"name":
    "John"}` and therefore needs custom logic to be mapped to `Person("John")`.

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
        De-serialize the Service representation of an Entity (typically the value
        that is returned at prediction time) to an instance of one of the internal Entity
        classes in :class:`intents.model.entities`
        """

    @abstractmethod
    def to_service(self, entity: SystemEntityMixin) -> Any:
        """
        Serialize a System Entity instance into a Service representation (typically,
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
    fulfillment_messages: Dict[IntentResponseGroup, List[IntentResponse]]
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

class Connector(ABC):

    agent_cls: type(Agent)
    default_session: str
    default_language: str

    def __init__(self, agent_cls: type(Agent), default_session: str=None, default_language: str="en"):
        """
        Connect the given Agent to a Prediction Service.

        :param agent_cls: The Agent to connect
        :param default_session: A default session ID (conversation channel) for predictions
        :param default_language: A default language for predictions
        """
        if not default_session:
            default_session = f"py-{str(uuid1())}"
        
        self.agent_cls = agent_cls
        self.default_session = default_session
        self.default_language = default_language

    @abstractmethod
    def predict(self, message: str, session: str=None, language: str=None) -> Intent:
        """
        Predict the given User message in the given session using the given
        language. When `session` or `language` are None, `predict` will use the
        default values that are specified in :meth:`__init__`.

        *predict* will return an instance of `Intent`, representing the intent
        as it was predicted by the service.

        >>> from intents.connectors import DialogflowEsConnector
        >>> from example_agent import ExampleAgent
        >>> df = DialogflowEsConnector('/path/to/service-account.json', ExampleAgent)
        >>> df_result = df.predict("Hi, my name is Guido")
        user_name_give(user_name='Guido')
        >>> df_result.user_name
        "Guido"
        >>> df_result.fulfillment_text
        "Hi Guido, I'm Bot"
        >>> df_result.confidence
        0.86
        """

    @abstractmethod
    def trigger(self, intent: Intent, session: str=None, language: str=None) -> Intent:
        """
        Trigger the given Intent in the given session using the given language.
        When `session` or `language` are None, `predict` will use the default
        values that are specified in :meth:`__init__`.

        >>> from intents.connectors import DialogflowEsConnector
        >>> from example_agent import ExampleAgent, smalltalk
        >>> df = DialogflowEsConnector('/path/to/service-account.json', ExampleAgent)
        >>> df_result = df.trigger(smalltalk.agent_name_give(agent_name='Alice'))
        agent_name_give(agent_name='Alice')
        >>> df_result.fulfillment_text
        "Howdy Human, I'm Alice"
        >>> df_result.confidence
        1.0
        """

    @abstractmethod
    def export(self, destination: str):
        """
        Export the connected Agent in a format that can be read and imported
        natively by the Prediction service. For instance, the Dialogflow service
        will produce a ZIP export that can be imported from the Dialogflow
        console.

        :param destination: destination path of the exported Agent
        """
