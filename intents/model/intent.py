import logging
import dataclasses
from dataclasses import dataclass, field
from typing import List, Dict, Any, _GenericAlias

from intents.model import context, event, entity

logger = logging.getLogger(__name__)

#
# Fulfillment Messages
#

class FulfillmentMessage:
    """
    This is a base class for Intent Fulfillment Messages
    """

class TextFulfillmentMessage(str, FulfillmentMessage):
    """
    This is a simple text fulfillment message.
    """

#
# Intent
#

@dataclass
class IntentMetadata:
    name: str
    input_contexts: List[context._ContextMetaclass] # TODO: model
    output_contexts: List[context.Context] # TODO: model
    events: List[str]
    action: str = None
    end_of_conversation: bool = False
    intent_webhook_enabled: bool = False
    slot_filling_webhook_enabled: bool = False

class _IntentMetaclass(type):
    # @property
    # def metadata(cls) -> IntentMetadata:
    #     if not cls.metadata:
    #         raise ValueError(f"Intent {cls} has no metadata. You need to register it with @agent.intent before using it")
    #     return cls.metadata
    metadata: IntentMetadata = None

@dataclass
class IntentParameterMetadata:
    name: str
    entity_cls: entity._EntityMetaclass
    is_list: bool
    required: bool
    default: Any

class Intent(metaclass=_IntentMetaclass):
    """
    Represents a predicted intent. This is also used as a base class for the
    intent classes that model a Dialogflow Agent in Python code.

    TODO: check parameter names: no underscore, no reserved names, max length
    """

    @dataclass
    class Meta:
        """
        This is a simpler form of :class:`IntentMetadata`. It is used to specify
        optional metadata when creating Intent classes, without interfering with
        those that are managed by :class:`Agent`.

        TODO: consider merging with IntentMetadata: currently the only
        Agent-managed fields are "name" and "events"
        """
        input_contexts: List[context._ContextMetaclass] = field(default_factory=list)
        output_contexts: List[context.Context] = field(default_factory=list)
        additional_events: List[event.Event] = field(default_factory=list)

    # User fills this with desired extra metadata
    meta: Meta = None

    # :class:`Agent` fills this, integrating Intent.meta with managed fields
    # TODO: make private, with a @property getter
    metadata: IntentMetadata = None
    _df_response = None

    # A :class:`PredictionService` provides this
    prediction: 'intents.Prediction'

    @property
    def confidence(self) -> float:
        return self.prediction.confidence

    @property
    def contexts(self) -> list:
        return self.prediction.contexts

    @property
    def fulfillment_text(self) -> str:
        return self.prediction.fulfillment_text

    def fulfillment_messages(self) -> List[FulfillmentMessage]:
        return self.prediction.fulfillment_messages

    # def fulfillment_messages(self, platform: FulfillmentMessagePlatform=None) -> List[FulfillmentMessage]:
    #     if not platform:
    #         platform = FulfillmentMessagePlatform.PLATFORM_UNSPECIFIED

    #     result_per_platform = defaultdict(list)
    #     for m in self._prediction.fulfillment_messages:
    #         m_platform = FulfillmentMessagePlatform(m.platform)
    #         result_per_platform[m_platform].append(build_response_message(m))

    #     return result_per_platform[platform]

    @classmethod
    def parameter_schema(cls) -> Dict[str, IntentParameterMetadata]:
        """
        Return a dict representing the Intent parameter definition. A key is a
        parameter name, a value is a :class:`IntentParameterMetadata` object.

        TODO: consider computing this in metaclass to cache value and check types
        """
        result = {}
        for param_field in cls.__dict__['__dataclass_fields__'].values():
            # List[...]
            if isinstance(param_field.type, _GenericAlias):
                if param_field.type.__dict__.get('_name') != 'List':
                    raise ValueError(f"Invalid typing '{param_field.type}' for parameter '{param_field.name}'. Only 'List' is supported.")

                if len(param_field.type.__dict__.get('__args__')) != 1:
                    raise ValueError(f"Invalid List modifier '{param_field.type}' for parameter '{param_field.name}'. Must define exactly one inner type (e.g. 'List[Sys.Any]')")
                
                # From here on, check the inner type (e.g. List[Sys.any] -> Sys.Any)
                entity_cls = param_field.type.__dict__.get('__args__')[0]
                is_list = True
            else:
                entity_cls = param_field.type
                is_list = False

            required = isinstance(param_field.default, dataclasses._MISSING_TYPE)
            result[param_field.name] = IntentParameterMetadata(
                name=param_field.name,
                entity_cls=entity_cls,
                is_list=is_list,
                required=required,
                default=param_field.default if not required else '',
            )

        return result

    @classmethod
    def from_prediction(cls, prediction: 'intents.Prediction') -> 'Intent':
        """
        Build an :class:`Intent` class from a :class:`Prediction`. In practice:

        #. Match parameters givent the Intent schema
        #. Instantiate the Intent
        #. Set the `prediction` field on the instantiated Intent.
        """
        try:
            parameters = prediction.parameters(cls.parameter_schema())
        except ValueError as exc:
            raise ValueError(f"Failed to match parameters for Intent class '{cls}'. Prediction: {prediction}") from exc

        result = cls(**parameters)
        result.prediction = prediction
        return result
