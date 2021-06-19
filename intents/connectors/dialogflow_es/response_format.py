"""
Here we define schemas and utilities to convert Dialogflow Response elements to
*Intents* native classes.

TODO: consider using same schemas (e.g. for response messages) in Agent export
"""
from typing import Dict, List
from collections import defaultdict
from abc import ABC, abstractmethod

from google.cloud.dialogflow_v2 import types as df_types
from google.protobuf.json_format import MessageToDict

from intents.language import IntentResponseGroup, IntentResponse, TextIntentResponse, QuickRepliesIntentResponse, CardIntentResponse

class DialogflowIntentResponse(ABC):
    """
    An interface to add IntentResponse de-serialization from messages in
    Dialogflow Responses. 
    """

    @classmethod
    def from_df_message(cls, df_message_data: df_types.intent.Intent.Message) -> IntentResponse:
        """
        Build the IntentResponse from a DialogflowResult
        """
        raise NotImplementedError()

class DialogflowTextResponse(TextIntentResponse, DialogflowIntentResponse):

    @classmethod
    def from_df_message(cls, df_message_data: df_types.intent.Intent.Message) -> TextIntentResponse:
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
        message_dict = MessageToDict(df_message_data._pb)
        assert isinstance(message_dict["text"], list)
        return TextIntentResponse(
            choices=message_dict["text"]
        )

class DialogflowQuickRepliesResponse(QuickRepliesIntentResponse, DialogflowIntentResponse):

    @classmethod
    def from_df_message(cls, df_message_data: df_types.intent.Intent.Message) -> TextIntentResponse:
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
        message_dict = MessageToDict(df_message_data._pb)
        return QuickRepliesIntentResponse(
            replies=message_dict["quickReplies"]
        )

class DialogflowCardResponse(CardIntentResponse, DialogflowIntentResponse):

    @classmethod
    def from_df_message(cls, df_message_data: df_types.intent.Intent.Message) -> CardIntentResponse:
        message_dict = MessageToDict(df_message_data._pb)
        message_buttons = message_dict.get("buttons", [])
        card_link = message_buttons[0].get('postback') if message_buttons else None
        return CardIntentResponse(
            title=message_dict.get("title"),
            subtitle=message_dict.get("subtitle"),
            image=message_dict.get("imageUri"),
            link=card_link
        )

def build_response_message(df_message):
    """
    Build a fulfillment message from a protobuf structure, as it is found in a
    protobuf response (`query_result.fulfillment_messages`)
    """
    if df_message.text:
        return DialogflowTextResponse.from_df_message(df_message.text)
    if df_message.quick_replies:
        return DialogflowQuickRepliesResponse.from_df_message(df_message.quick_replies)
    if df_message.card:
        return DialogflowCardResponse.from_df_message(df_message.card)

    raise ValueError(f"Unsupported Fulfillment Message: {df_message}")

def intent_responses(df_response: df_types.DetectIntentResponse) -> Dict[IntentResponseGroup, List[IntentResponse]]:
    """
    Return the responses in the prediction as standard instances of
    :class:`IntentResponse` and grouped by response group
    (:var:`IntentResponseGroup.DEFAULT` or :var:`IntentResponseGroup.RICH`) 
    """
    result = defaultdict(list)
    for message in df_response.query_result.fulfillment_messages:
        if message.platform == df_types.intent.Intent.Message.Platform.PLATFORM_UNSPECIFIED:
            group = IntentResponseGroup.DEFAULT
        else:
            group = IntentResponseGroup.RICH

        result[group].append(build_response_message(message))
    return dict(result)
