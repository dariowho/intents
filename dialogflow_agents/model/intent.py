import logging
from dataclasses import dataclass
from typing import List

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

    _confidence = None
    @property
    def confidence(self):
        return self._confidence

    _contexts = None
    @property
    def contexts(self):
        return self._contexts

    @classmethod
    def from_df_response(cls, df_response) -> 'Intent':
        # 'parameter_name' -> type
        parameter_definition = cls.__dict__.get('__annotations__', {})

        df_parameters = df_response['queryResult']['parameters']
        if parameter_definition:
            logger.debug("Parameters found in class %s", cls)
            result = cls(**df_parameters)
        elif df_parameters:
            raise ValueError(f"Found parameters in Dialogflow Response, but class {cls} doesn't take any: {df_response}")
        
        # TODO: assert intent name matches intent class
        result._confidence = df_response['queryResult']['intentDetectionConfidence']
        result._contexts = df_response.get('outputContexts', {})

        return result
