"""
Connectors allow *Intents* Agent definitions to operate with real cloud services
such as Dialogflow, Lex or Azure Bot Services. Currently, only one connector is
provided with this library, and this is for Dialogflow ES:
:mod:`intents.connectors.dialogflow_es.connector`.

.. note::

    Details about the Connector interface are only useful if you need to develop your own Service Connector (please consider raising a pull request if this is the case). If you just need to use the included Dialogflow Connector you can jump to its documentation page right away: :mod:`intents.connectors.dialogflow_es.connector`

Connectors are used to operate with the cloud version of the Agent, and
specifically to:

* Export an :class:`intents.Agent` in a format that is natively readable by the
  Service
* Predict User messages on the Cloud Agent
* Trigger Intents on the Cloud Agent

More details can be found in the :class:`Connector` interface.
"""
import logging
import warnings
from uuid import uuid1
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union
from dataclasses import dataclass, field

from intents import Intent, Agent, Entity
from intents.model.fulfillment import FulfillmentRequest
from intents.types import IntentType, EntityType
from intents.language import IntentResponseDict, LanguageCode, ensure_language_code, agent_supported_languages
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
    def entity_cls(self) -> EntityType:
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
    This is a convenience :class:`EntityMapping` that reads values as they are sent
    by the prediction service (e.g. `"3"` -> `Sys.Integer("3")`), and serializes
    by simple string conversion (e.g. `Sys.Integer(3)` -> "3").

    The System Entity to use must be defined when instantiating the mapping, for
    instance:

    >>> StringEntityMapping(Sys.Integer, "sys.number-integer")

    Args:
        entity_cls: One of the `Sys.*` entity classes
        service_name: Name of the corresponding entity within the Prediction
            Service
    """

    entity_cls: EntityType = None
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
    instance, :class:`Sys.Color` can be patched with
    :class:`intents.resources.builtin_entities.color.I_IntentsColor`.
    `PatchedEntityMapping` can be use to define mappings for system entities
    that are patched with custom ones.

    Connectors that use patched entities must define logic to handle
    `PatchedEntityMapping` in their export procedures.

    By default, `builtin_entity.name` is used as Service entity name, and values
    are (de)serialized as simple strings. If a Connector have different
    required, it should define a custom subclass of `PatchedEntityMapping`.
    """
    entity_cls: EntityType = None
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
    Models a list of entity mappings, in the form of a dict where the key is a
    System entity class (inherits from :class:`SystemEntityMixin`) and the value
    is a :class:`EntityMapping`. In addition to a standard dict, these features
    are added:

    * Instantiate from a list of mappings with :meth:`from_list`
    * Flexible lookup with :meth:`ServiceEntityMapping.lookup`
    """

    def lookup(self, entity_cls: EntityType) -> EntityMapping:
        """
        Return the mapping in the dictionary that is associated with the given
        `entity_cls`. In addition to a simple `mappings[entity_cls]`, this
        method also implements a fallback for Custom Entities. That is, when a
        Custom Entity is not in the mapping dict (typically they are not),
        retrieve the mapping for :class:`Entity` instead.

        Args:
            entity_cls: The Entity class to lookup
        Returns:
            The mapping that refers to the given Entity class
        Raises:
            KeyError: If no mapping exists that can be used for `entity_cls`
        """
        # `Entity` objects are custom entities
        if issubclass(entity_cls, Entity) and entity_cls not in self:
            entity_cls = Entity
        if entity_cls not in self:
            mapped_entities = [m.entity_cls for m in self]
            raise KeyError(f"Failed to lookup entity {entity_cls} in mappings. Mapped entities: {mapped_entities}")
        return self[entity_cls]

    def is_mapped(self, entity_cls: EntityType, lang: LanguageCode) -> bool:
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

@dataclass
class Prediction:
    """
    One of the core uses of Service Connectors is to predict user utterances, or
    programmatically trigger intents. This class models the result of such
    predictions and triggers.

    You will typically obtain `Prediction` objects from :class:`Connector`
    methods :meth:`~Connector.predict` and :meth:`~Connector.trigger`.

    Args:
        intent: An instance of the predicted Intent
        confidence: A confidence value on the service prediction
        fulfillment_messages: A map of Intent Responses, as they were
            returned by the Service.
        fulfillment_text: A plain-text version of the response
    """
    intent: Intent
    confidence: float
    fulfillment_messages: IntentResponseDict = field(repr=False)
    fulfillment_text: str = None

    @property
    def fulfillment_message_dict(self):
        warnings.warn("Prediction.fulfillment_message_dict is deprecated. Please update "
                      "your code to use Prediction.fulfillment_messages instead.", DeprecationWarning)
        return self.fulfillment_messages

def deserialize_intent_parameters(
    service_parameters: Dict[str, Any],
    intent_cls: IntentType,
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
            raise ValueError(f"Found parameter {param_name} in Service Prediction, but Intent class does not define it.")
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

class Connector(ABC):
    """
    Connect the given Agent to a Prediction Service.

    Args:
        agent_cls: The Agent to connect
        default_session: A default session ID (conversation channel) for predictions
        default_language: A default language for predictions. If None, Connector
            will use the Agent's firs defined language.
    """
    agent_cls: type(Agent)
    default_session: str
    default_language: str

    def __init__(
        self,
        agent_cls: type(Agent),
        default_session: str=None,
        default_language: Union[LanguageCode, str]=None
    ):
        if not default_language:
            default_language = agent_supported_languages(agent_cls)[0]
        default_language = ensure_language_code(default_language)
        
        if not default_session:
            default_session = f"py-{str(uuid1())}"
        
        self.agent_cls = agent_cls
        self.default_session = default_session
        self.default_language = default_language

    @property
    @abstractmethod
    def entity_mappings(self) -> ServiceEntityMappings:
        """
        A Service Connector must know the Entity Mappings of its Prediction
        Service. They will be used to lookup entity names during export.
        """

    @abstractmethod
    def predict(self, message: str, session: str=None, language: Union[LanguageCode, str]=None) -> Prediction:
        """
        Predict the given User message in the given session using the given
        language. When `session` or `language` are None, `predict` will use the
        default values that are specified in :meth:`__init__`.

        *predict* will return an instance of :class:`Prediction`, representing
        the service response.

        >>> from intents.connectors import DialogflowEsConnector
        >>> from example_agent import ExampleAgent
        >>> df = DialogflowEsConnector('/path/to/service-account.json', ExampleAgent)
        >>> prediction = df.predict("Hi, my name is Guido")
        >>> prediction.intent
        UserNameGive(user_name='Guido')
        >>> prediction.intent.user_name
        "Guido"
        >>> prediction.fulfillment_text
        "Hi Guido, I'm Bot"
        >>> prediction.confidence
        0.86

        Args:
            message: The User message to predict
            session: Any string identifying a conversation
            language: A LanguageCode object, or a ISO 639-1 string (e.g. "en")
        """

    @abstractmethod
    def trigger(self, intent: Intent, session: str=None, language: Union[LanguageCode, str]=None) -> Prediction:
        """
        Trigger the given Intent in the given session using the given language.
        When `session` or `language` are None, `predict` will use the default
        values that are specified in :meth:`__init__`.

        >>> from intents.connectors import DialogflowEsConnector
        >>> from example_agent import ExampleAgent, smalltalk
        >>> df = DialogflowEsConnector('/path/to/service-account.json', ExampleAgent)
        >>> prediction = df.trigger(smalltalk.AgentNameGive(agent_name='Alice'))
        >>> prediction.intent
        AgentNameGive(agent_name='Alice')
        >>> prediction.fulfillment_text
        "Howdy Human, I'm Alice"
        >>> prediction.confidence
        1.0

        Args:
            intent: The Intent instance to trigger
            session: Any string identifying a conversation
            language: A LanguageCode object, or a ISO 639-1 string (e.g. "en")
        """

    @abstractmethod
    def fulfill(self, fulfillment_request: FulfillmentRequest) -> dict:
        """
        This method is responsible for handling requests coming from a
        fulfillment interface. We are at that point in the flow when an intent
        was triggered/predicted, and Service is calling the webhook service for
        fulfillment.

        In this method, Connector interprets the body of the request, builds a
        :class:`~intents.model.fulfillment.FulfillmentContext` object, builds
        the :class:`~intents.model.Intent` object that is references in the
        request, and calls its :meth:`~intents.model.intent.Intent.fulfill`
        method.

        This will produce a
        :class:`~intents.model.fulfillment.FulfillmentResult` object, that
        Connector will translate into a Service-compatible response (a
        dictionary) and return to caller.

        Args:
            fulfillment_request: A raw fulfillment request, as it is sent by the
                Prediction service (typically via a standard REST webhook call)
        Returns:
            An object containing a response that Service can read
        """

    @abstractmethod
    def upload(self):
        """
        Upload the connected Agent to the Prediction Service.
        """

    @abstractmethod
    def export(self, destination: str):
        """
        Export the connected Agent in a format that can be read and imported
        natively by the Prediction service. For instance, the Dialogflow service
        will produce a ZIP export that can be imported from the Dialogflow
        console.

        Note that you can also directly upload the Agent with :meth:`upload`.

        :param destination: destination path of the exported Agent
        """

    def _entity_service_name(self, entity_cls: SystemEntityMixin) -> str:
        """
        Return the name of the given entity in the specific service; this can be
        the class name itself, or an :class:`EntityMapping` lookup in the case
        of System Entities.

        For instance, a :class:`Sys.Person` Entity will need to be looked up in
        the mappings to find out its service name (`sys.person` in Dialogflow,
        `AMAZON.Person` in Alexa, and so on). A custom entity (e.g. `PizzaType`)
        can use its class name instead.
        """
        if issubclass(entity_cls, SystemEntityMixin):
            return self.entity_mappings[entity_cls].service_name
        return entity_cls.name
