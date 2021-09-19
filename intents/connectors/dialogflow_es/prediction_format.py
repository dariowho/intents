"""
Here we define schemas and utilities to convert Dialogflow Response elements to
*Intents* native classes.

References:

* Webhooks Request/Response
    * https://cloud.google.com/dialogflow/es/docs/fulfillment-webhook#webhook_request
    * https://cloud.google.com/dialogflow/es/docs/reference/rpc/google.cloud.dialogflow.v2#webhookrequest
    * https://cloud.google.com/dialogflow/es/docs/fulfillment-webhook#webhook_response

TODO: consider using same schemas (e.g. for response messages) in Agent export
"""
from enum import Enum
from typing import Dict, List, Any
from dataclasses import dataclass, field
from collections import defaultdict
from abc import ABC, abstractmethod

import dacite
from google.cloud.dialogflow_v2 import types as df_types
from google.protobuf.json_format import MessageToDict

#
# Response Format
#

@dataclass
class QueryResultMessageText:
    text: List[str]

@dataclass
class QueryResultMessageImage:
    imageUri: str
    accessibilityText: str = ""

@dataclass
class QueryResultMessageQuickReplies:
    quickReplies: List[str]
    title: str = ""

@dataclass
class QueryResultMessageCardButtons:
    text: str = ""
    postback: str = ""

@dataclass
class QueryResultMessageCard:
    title: str = ""
    subtitle: str = ""
    imageUri: str = ""
    buttons: List[QueryResultMessageCardButtons] = field(default_factory=list)

@dataclass
class QueryResultMessagePayload:
    payload: Dict[str, Any]

class QueryResultMessagePlatform(Enum):
    """
    Ref:
    https://cloud.google.com/dialogflow/es/docs/reference/rpc/google.cloud.dialogflow.v2#google.cloud.dialogflow.v2.Intent.Message.Platform
    """
    PLATFORM_UNSPECIFIED = "PLATFORM_UNSPECIFIED"
    FACEBOOK = "FACEBOOK"
    SLACK = "SLACK"
    TELEGRAM = "TELEGRAM"
    KIK = "KIK"
    SKYPE = "SKYPE"
    LINE = "LINE"
    VIBER = "VIBER"
    ACTIONS_ON_GOOGLE = "ACTIONS_ON_GOOGLE"
    GOOGLE_HANGOUTS = "GOOGLE_HANGOUTS"

@dataclass
class QueryResultMessage:
    """
    See
    https://cloud.google.com/dialogflow/es/docs/reference/rpc/google.cloud.dialogflow.v2#message
    """
    platform: QueryResultMessagePlatform = QueryResultMessagePlatform.PLATFORM_UNSPECIFIED
    text: QueryResultMessageText = None
    image: QueryResultMessageImage = None
    quickReplies: QueryResultMessageQuickReplies = None
    card: QueryResultMessageCard = None
    payload: QueryResultMessagePayload = None

@dataclass
class QueryResultContext:
    name: str
    lifespanCount: int = 0
    parameters: Dict[str, Any] = field(default_factory=dict)

    @property
    def simple_name(self):
        """
        Dialogflow will store a full context path in QueryResultContext.name.
        The last chunk is just the context name.
        """
        return self.name.split('/')[-1]

@dataclass
class QueryResultIntent:
    name: str
    displayName: str

@dataclass
class QueryResult:
    queryText: str
    languageCode: str
    parameters: Dict[str, Any] = None
    intent: QueryResultIntent = None
    intentDetectionConfidence: float = None
    fulfillmentText: str = ""
    fulfillmentMessages: List[QueryResultMessage] = field(default_factory=list)
    allRequiredParamsPresent: bool = False
    outputContexts: List[QueryResultContext] = field(default_factory=list)
    action: str = ""
    diagnosticInfo: dict = field(default_factory=dict)
    webhookPayload: dict = field(default_factory=dict) # TODO: model
    webhookSource: str = ''
    cancelsSlotFilling: bool = False
    speechRecognitionConfidence: float = None

@dataclass
class DetectIntentResponseWebhookStatus:
    code: int
    message: str
    details: List[Any] = field(default_factory=list)

@dataclass
class DetectIntentResponse:
    responseId: str
    queryResult: QueryResult
    webhookStatus: DetectIntentResponseWebhookStatus = None
    outputAudio: Any = None
    outputAudioConfig: dict = None # TODO: model

@dataclass
class WebhookRequest:
    session: str
    responseId: str
    queryResult: QueryResult
    originalDetectIntentRequest: dict = None

def from_dict(data_class: type, data: dict):
    """
    Wraps :func:`dacite.from_dict` configuring enums for Dialogflow Predictions

    Args:
        data_class: The dataclass to use as schema
        data: Will be converted into a dataclass instance
    """
    return dacite.from_dict(
        data_class=data_class,
        data=data,
        config=dacite.Config(cast=[QueryResultMessagePlatform])
    )

def from_protobuf(data_class: type, data):
    """
    Cast a protobuf structure to an equivalent dataclass type. We like dataclasses.
    """
    if hasattr(data, "_pb"):
        data_dict = MessageToDict(data._pb)
    else:
        data_dict = MessageToDict(data)
    return from_dict(data_class, data_dict)
