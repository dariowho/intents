import logging
from abc import ABC
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Union, Tuple

from google.protobuf.json_format import MessageToDict
from google.cloud.dialogflow_v2 import types as pb

from intents.connectors.dialogflow_es import prediction_format as df
from intents.language import IntentResponseGroup, IntentResponseDict, IntentResponse, TextIntentResponse, QuickRepliesIntentResponse, ImageIntentResponse, CardIntentResponse

logger = logging.getLogger(__name__)

@dataclass
class DfResponseContextParameter:
    value: Union[str, dict]=None
    original: str=None

@dataclass
class DfResponseContext:
    name: str
    full_name: str
    lifespan: int
    parameters: Dict[str, DfResponseContextParameter]

class PredictionBody:
    """
    This is a superclass for :class:`DetectIntentBody` and
    :class:`WebhookRequestBody`, which both send a `query_result` field
    """
    
    queryResult: df.QueryResult # This field is common in webhook
                                # requests and detectintent responses

    context_lifespans: Dict[str, int]

    def __init__(self, query_result: df.QueryResult):
        self.queryResult = query_result
        self.context_lifespans = {c.simple_name: c.lifespanCount for c in query_result.outputContexts}

    @property
    def intent_name(self):
        return self.queryResult.intent.displayName

    @property
    def intent_parameters(self):
        return self.queryResult.parameters

    def contexts(self) -> Tuple[Dict[str, DfResponseContext], Dict[str, DfResponseContextParameter]]:
        """
        Return a "context_name -> Context" dict of the context in the given
        response, and a dict of global parameter values. In Dialogflow, parameters
        with the same name are overwritten in all contexts, even if they come from
        different intents. Because of this, we can build a map of all global names
        and their values

        TODO: cover less frequent cases (Event/context parameter source,
        event/context/constant parameter default, ...)

        TODO: cache

        :return: A dict of Contexts, A dict of global parameter values
        """
        result_contexts = {}

        for c in self.queryResult.outputContexts:
            parameters: Dict[str, DfResponseContextParameter] = defaultdict(DfResponseContextParameter)
            for p_name, p_value in c.parameters.items():
                if p_name.endswith(".original"):
                    p_name = p_name[:-9]
                    parameters[p_name].original = p_value
                else:
                    parameters[p_name].value = p_value

            context = DfResponseContext(
                name=c.simple_name,
                full_name=c.name,
                lifespan=c.lifespanCount,
                parameters=parameters
            )
            result_contexts[context.name] = context

        result_parameters = _build_global_context_parameters(result_contexts)

        return result_contexts, result_parameters

class DetectIntentBody(PredictionBody):
    """
    This is the result of an intent prediction, exactly as it is sent by
    Dialogflow. Note that the original protobuf is marshaled and converted to
    dataclass, but its field names and content are the same. 
    """
    detect_intent: df.DetectIntentResponse

    def __init__(self, detect_intent_protobuf: pb.DetectIntentResponse):
        detect_intent_dict = MessageToDict(detect_intent_protobuf._pb, including_default_value_fields=True)
        self.detect_intent = df.from_dict(
            data_class=df.DetectIntentResponse,
            data=detect_intent_dict,
        )
        super().__init__(self.detect_intent.queryResult)

class WebhookRequestBody(PredictionBody):
    """
    This is a fulfillment webhook request that Dialogflow sends us.

    Note that, even though there are protobuf schemas for webhook requests
    (`pb.WebhookRequest`), this class is instantiated with a dict. This is
    because webhook requests typically come from REST calls that Dialogflow
    makes to a fulfillment endpoint.
    """
    webhook_request: df.WebhookRequest

    def __init__(self, webhook_request_dict: dict):
        self.webhook_request = df.from_dict(
            data_class=df.WebhookRequest,
            data=webhook_request_dict,
        )
        super().__init__(self.webhook_request.queryResult)

def _build_global_context_parameters(
    contexts: Dict[str, DfResponseContext]
) -> Dict[str, DfResponseContextParameter]:
    result = {}
    for c in contexts.values():
        for p_name, p_value in c.parameters.items():
            if p_name in result and result[p_name] != p_value:
                logger.warning("Parameter '%s' has different value in existing context. " +
                    "This may cause unexpected behavior. Current value: %s. Existing " +
                    "value: %s.", p_name, p_value, result[p_name])
            result[p_name] = p_value
    return result

#
# Response Messages
#

class DialogflowIntentResponse(ABC):
    """
    An interface to add IntentResponse de-serialization from messages in
    Dialogflow Responses. 
    """

    @classmethod
    def from_df_message(cls, df_message: df.QueryResultMessage) -> IntentResponse:
        """
        Build the IntentResponse from a DialogflowResult
        """
        raise NotImplementedError()

class DialogflowTextResponse(TextIntentResponse, DialogflowIntentResponse):

    @classmethod
    def from_df_message(cls, df_message: df.QueryResultMessage) -> TextIntentResponse:
        """
        .. code-block:: json

            {
                "text": {
                    "text": [
                        "Hello, Human"
                    ]
                }
            }
        """
        choices = df_message.text.text
        assert isinstance(choices, list)
        return TextIntentResponse(
            choices=choices
        )

class DialogflowQuickRepliesResponse(QuickRepliesIntentResponse, DialogflowIntentResponse):

    @classmethod
    def from_df_message(cls, df_message: df.QueryResultMessage) -> TextIntentResponse:
        """
        .. code-block: json
            
            {
                "title": "Quick Replies",
                "quickReplies": [
                    "Recommend an hotel",
                    "Send holiday photo"
                ]
            }
        """
        return QuickRepliesIntentResponse(
            replies=df_message.quickReplies.quickReplies
        )

class DialogflowImageResponse(ImageIntentResponse, DialogflowIntentResponse):

    @classmethod
    def from_df_message(cls, df_message: df.QueryResultMessage) -> TextIntentResponse:
        """
        .. code-block: json
            
            {
                "imageUri": "https://www.example.com/image.png",
                "accessibilityText": "An example image"
            }
        """
        return ImageIntentResponse(
            url=df_message.image.imageUri,
            title=df_message.image.accessibilityText
        )

class DialogflowCardResponse(CardIntentResponse, DialogflowIntentResponse):

    @classmethod
    def from_df_message(cls, df_message: df.QueryResultMessage) -> CardIntentResponse:        
        message_buttons = df_message.card.buttons
        card_link = message_buttons[0].postback if message_buttons else None
        return CardIntentResponse(
            title=df_message.card.title,
            subtitle=df_message.card.subtitle,
            image=df_message.card.imageUri,
            link=card_link
        )

def build_response_message(df_message: df.QueryResultMessage):
    """
    Build a fulfillment message from a protobuf structure, as it is found in a
    protobuf response (`query_result.fulfillment_messages`)
    """
    if df_message.text:
        return DialogflowTextResponse.from_df_message(df_message)
    if df_message.quickReplies:
        return DialogflowQuickRepliesResponse.from_df_message(df_message)
    if df_message.card:
        return DialogflowCardResponse.from_df_message(df_message)
    if df_message.image:
        return DialogflowImageResponse.from_df_message(df_message)
    # TODO: custom payload

    raise ValueError(f"Unsupported Fulfillment Message: {df_message}")

def intent_responses(df_body: PredictionBody) -> IntentResponseDict:
    """
    Return the responses in the prediction as standard instances of
    :class:`IntentResponse` and grouped by response group
    (:var:`IntentResponseGroup.DEFAULT` or :var:`IntentResponseGroup.RICH`) 
    """
    result = defaultdict(list)
    for message in df_body.queryResult.fulfillmentMessages:
        if message.platform == df.QueryResultMessagePlatform.PLATFORM_UNSPECIFIED:
            group = IntentResponseGroup.DEFAULT
        else:
            group = IntentResponseGroup.RICH

        result[group].append(build_response_message(message))
    return dict(result)
