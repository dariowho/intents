import logging
from dataclasses import dataclass, field
from typing import List

from dialogflow_agents.model import context, event

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
    prediction: 'dialogflow_agents.Prediction'

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
    def from_prediction(cls, prediction: 'dialogflow_agents.Prediction') -> 'Intent':
        parameter_definition = cls.__dict__.get('__annotations__', {})
        if parameter_definition:
            logger.debug("Parameters found in class %s", cls)
            result = cls(**prediction.parameters_dict) # TODO: convert types
        elif prediction.parameters_dict:
            raise ValueError(f"Found parameters in Service Prediction, but class {cls} doesn't take any: {prediction}")
        else:
            result = cls()

        result.prediction = prediction
        return result
