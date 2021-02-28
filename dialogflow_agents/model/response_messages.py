import logging
from abc import ABC, abstractclassmethod

from google.cloud.dialogflow_v2 import types

logger = logging.getLogger(__name__)

FulfillmentMessagePlatform = types.Intent.Message.Platform

def build_response_message(protobuf):
    if protobuf.HasField('text'):
        return TextFulfillmentMessage.from_df_response(protobuf)
    else:
        raise ValueError("Unsupported Fulfillment Message: %s", protobuf)

class FulfillmentMessage(ABC):

    @abstractclassmethod
    def from_df_response(cls, protobuf):
        """
        Receive the Protobuf equivalent of the following dict:

        ```
        {
            "text": {
                "text": [
                    "Nice to meet you Dario!"
                ]
            }
        }
        ```

        Return a :class:`FulfillmentMessage` instance
        """
        pass

class TextFulfillmentMessage(str, FulfillmentMessage):
    """
    https://cloud.google.com/dialogflow/es/docs/reference/rpc/google.cloud.dialogflow.v2#text
    
    We ignore, the fact that `text` is defined as a list: Dialogflow responses
    only have one.
    """

    @classmethod
    def from_df_response(cls, protobuf):
        text_list = protobuf.text.text
        if len(text_list) == 0:
            return cls('')
        if len(text_list) > 1:
            logger.warning('Text Dialogflow response contains more than one text option, only the first will be considered: %s', protobuf)
        return cls(protobuf.text.text[0])
