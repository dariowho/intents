import logging
from dataclasses import dataclass
from typing import List, Dict
from collections import defaultdict

from google.protobuf.json_format import MessageToDict
from google.cloud.dialogflow_v2.types import DetectIntentResponse

from dialogflow_agents.model.response_messages import FulfillmentMessagePlatform, build_response_message, FulfillmentMessage

logger = logging.getLogger(__name__)

@dataclass
class IntentMetadata:
    name: str
    input_contexts: List[None] # TODO: model
    output_contexts: List[None] # TODO: model
    events: List[str]
    action: str = None
    end_of_conversation: bool = False
    intent_webhook_enabled: bool = False
    slot_filling_webhook_enabled: bool = False

class IntentMetaclass(type):
    # @property
    # def metadata(cls) -> IntentMetadata:
    #     if not cls.metadata:
    #         raise ValueError(f"Intent {cls} has no metadata. You need to register it with @agent.intent before using it")
    #     return cls.metadata
    metadata: IntentMetadata = None

class Intent(metaclass=IntentMetaclass):
    """
    Represents a predicted intent. This is also used as a base class for the
    intent classes that model a Dialogflow Agent in Python code.

    TODO: check parameter names: no underscore, no reserved names
    """

    metadata: IntentMetadata = None
    _df_response = None

    @property
    def confidence(self) -> float:
        return self._df_response.query_result.intent_detection_confidence

    @property
    def contexts(self) -> list:
        return MessageToDict(self._df_response.output_contexts)

    @property
    def fulfillment_text(self) -> str:
        return self._df_response.query_result.fulfillment_text

    def fulfillment_messages(self, platform: FulfillmentMessagePlatform=None) -> List[FulfillmentMessage]:
        if not platform:
            platform = FulfillmentMessagePlatform.PLATFORM_UNSPECIFIED

        result_per_platform = defaultdict(list)
        for m in self._df_response.query_result.fulfillment_messages:
            m_platform = FulfillmentMessagePlatform(m.platform)
            result_per_platform[m_platform].append(build_response_message(m))

        return result_per_platform[platform]

    @classmethod
    def from_df_response(cls, df_response: DetectIntentResponse) -> 'Intent':
        # 'parameter_name' -> type
        parameter_definition = cls.__dict__.get('__annotations__', {})
        
        # will convert snake_case to lowerCamelCase <rant> so API is documented
        # snake_case, protobuf is snake_case, dialogflow results are camelCase,
        # protobuf converted to dict is camelCase (unless you use a flag,
        # in that case it could also be snake_case) 💀 This is one of the
        # reasons this library exists </rant>
        df_response_dict = MessageToDict(df_response)

        df_parameters_dict = MessageToDict(df_response.query_result.parameters)
        if parameter_definition:
            logger.debug("Parameters found in class %s", cls)
            result = cls(**df_parameters_dict)
        elif df_parameters_dict:
            raise ValueError(f"Found parameters in Dialogflow Response, but class {cls} doesn't take any: {df_response}")
        
        # TODO: assert intent name matches intent class
        result._df_response = df_response

        return result
