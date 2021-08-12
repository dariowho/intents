"""
Here we define schemas to parse Alexa fulfillment requests into dataclasses
"""
from enum import Enum
from datetime import datetime
from typing import List, Dict, Any, Union
from dataclasses import dataclass, field

import dacite

from intents.helpers.data_classes import OmitNone


class IntentConfirmationStatus(Enum):
    NONE = "NONE"
    CONFIRMED = "CONFIRMED"
    DENIED = "DENIED"

class SlotType(Enum):
    SIMPLE = "Simple"
    LIST = "List"

@dataclass
class IntentSlotValueResolutionItemValueValue:
    id: str
    name: str

@dataclass
class IntentSlotValueResolutionItemValue:
    value: IntentSlotValueResolutionItemValueValue # ☠

@dataclass
class IntentSlotValueResolutionItem:
    authority: str
    status: dict # TODO: model
    values: List[IntentSlotValueResolutionItemValue]

@dataclass
class IntentSlotValueResolution:
    resolutionsPerAuthority: List[IntentSlotValueResolutionItem]

@dataclass
class IntentSlotValue:
    type: SlotType
    value: str = None # Only included when type=SIMPLE
    values: List["IntentSlotValue"] = None # Only included when type=LIST
    resolutions: IntentSlotValueResolution = None

@dataclass
class IntentSlot:
    confirmationStatus: IntentConfirmationStatus
    name: str
    # The following seem to be None when slot is returned but not matched
    source: str = None # always USER...
    slotValue: IntentSlotValue = None
    value: str = None
    resolutions: dict = None # model


#############
# RESPONSE  #
#############

class OutputSpeechType(Enum):
    PlainText = "PlainText"
    SSML = "SSML"

class PlayBehavior(Enum):
    ENQUEUE = "ENQUEUE"
    REPLACE_ALL = "REPLACE_ALL"
    REPLACE_ENQUEUED = "PlainText"

@dataclass
class FulfillmentResponseOutputSpeech:
    type: OutputSpeechType
    text: str = OmitNone()
    ssml: str = OmitNone()
    playBehavior = PlayBehavior

@dataclass
class FulfillmentResponseDirective:
    type: str

@dataclass
class FulfillmentResponseDialogDelegateUpdatedIntent:
    name: str
    confirmationStatus: IntentConfirmationStatus
    slots: Dict[str, IntentSlot]

@dataclass
class FulfillmentResponseDialogDelegateDirective(FulfillmentResponseDirective):
    type: str = "Dialog.Delegate"
    updatedIntent: FulfillmentResponseDialogDelegateUpdatedIntent=None

@dataclass
class FulfillmentResponse:
    outputSpeech: FulfillmentResponseOutputSpeech = None
    card: dict = OmitNone()    # TODO: model
    reprompt: dict = OmitNone()    # TODO: model
    shouldEndSession: bool = True
    directives: List[FulfillmentResponseDirective] = OmitNone() # TODO: model

@dataclass
class FulfillmentResponseBody:
    version: str = "1.0"
    sessionAttributes: dict = field(default_factory=dict)
    response: FulfillmentResponse=OmitNone()

#############
# REQUEST   #
#############

#
# Session
#

@dataclass
class FulfillmentSessionApplication:
    applicationId: str

@dataclass
class FulfillmentSessionUser:
    userId: str
    accessToken: str = None
    permissions: dict = None # deprecated: https://developer.amazon.com/en-US/docs/alexa/custom-skills/request-and-response-json-reference.html#session-object

@dataclass
class FulfillmentSession:
    new: bool
    sessionId: str
    application: FulfillmentSessionApplication
    user: FulfillmentSessionUser
    attributes: Dict[str, Any] = field(default_factory=dict)

#
# Context
# https://developer.amazon.com/en-US/docs/alexa/custom-skills/request-and-response-json-reference.html#context-object
#

class PlayerActivity(Enum):
    IDLE = "IDLE"
    PAUSED = "PAUSED"
    PLAYING = "PLAYING"
    BUFFER_UNDERRUN = "BUFFER_UNDERRUN"
    FINISHED = "FINISHED"
    STOPPED = "STOPPED"

@dataclass
class FulfillmentContextAudioPlayer:
    token: str
    playerActivity: PlayerActivity
    offsetInMilliseconds: float = None

# ------

@dataclass
class FulfillmentContextSystemApplication:
    applicationId: str

@dataclass
class FulfillmentContextSystemDevice:
    deviceId: str
    supportedInterfaces: Dict[str, dict] # TODO: model with Enum

@dataclass
class FulfillmentContextSystemUnit:
    unitId: str
    persistentUnitId: str

@dataclass
class FulfillmentContextSystemPerson:
    personId: str
    accessToken: str = None

@dataclass
class FulfillmentContextSystemUser:
    userId: str
    accessToken: str = None
    permissions: dict = None # deprecated

@dataclass
class FulfillmentContextSystem:
    apiAccessToken: str
    apiEndpoint: str
    application: FulfillmentContextSystemApplication # TODO: use this to verify that request is authentic
    device: FulfillmentContextSystemDevice
    user: FulfillmentContextSystemUser            # the person who owns the account that installed the skill
    person: FulfillmentContextSystemPerson = None # the person that is talking to Alexa (recognized by voice)
    unit: FulfillmentContextSystemUnit = None
    
# -----
# https://developer.amazon.com/en-US/docs/alexa/alexa-presentation-language/apl-interface.html#viewport-properties

class ViewportMode(Enum):
    HUB = "HUB"
    TV = "TV"
    PC = "PC"
    MOBILE = "MOBILE"
    AUTO = "AUTO"

class ViewportShape(Enum):
    ROUND = "ROUND"
    RECTANGLE = "RECTANGLE"

@dataclass
class FulfillmentContextViewportExperience:
    canRotate: bool
    canResize: bool

@dataclass
class FulfillmentContextViewport:
    experiences: List[FulfillmentContextViewportExperience]
    mode: ViewportMode
    shape: ViewportShape
    pixelHeight: int
    pixelWidth: int
    currentPixelHeight: int
    currentPixelWidth: int
    dpi: int
    touch: List[str] = None # TODO: model (no docs!)
    keyboard: List[str] = None # TODO: model
    video: dict = None # TODO: model

# -----

@dataclass
class FulfillmentContext:
    # "Alexa.Presentation.APL": ... ☠**☢ϟϟ☠☠☣
    System: FulfillmentContextSystem
    AudioPlayer: FulfillmentContextAudioPlayer = None
    Viewport: FulfillmentContextViewport = None
    Viewports: List[dict] = None # TODO: model

#
# Request
#

class RequestType(Enum):
    LAUNCH = "LaunchRequest"
    INTENT = "IntentRequest"
    SESSION_ENDED = "SessionEndedRequest"
    CAN_FULFILL_INTENT = "CanFulfillIntentRequest"

@dataclass
class FulfillmentRequest:
    type: RequestType
    requestId: str
    timestamp: datetime # TODO: timezone? This will be checked to prevent reply attacks
    locale: str

@dataclass
class FulfillmentLaunchRequest(FulfillmentRequest):
    pass

@dataclass
class FulfillmentIntentRequestIntent:
    name: str
    confirmationStatus: IntentConfirmationStatus
    slots: Dict[str, IntentSlot] = field(default_factory=dict)

@dataclass
class FulfillmentIntentRequest(FulfillmentRequest):
    intent: FulfillmentIntentRequestIntent
    dialogState: str = None

class SessionEndedReason(Enum):
    USER_INITIATED = "USER_INITIATED"
    ERROR = "ERROR"
    EXCEEDED_MAX_REPROMPTS = "EXCEEDED_MAX_REPROMPTS"

class SessionEndedErrorType(Enum):
    INVALID_RESPONSE = "INVALID_RESPONSE"
    DEVICE_COMMUNICATION_ERROR = "DEVICE_COMMUNICATION_ERROR"
    INTERNAL_SERVICE_ERROR = "INTERNAL_SERVICE_ERROR"
    ENDPOINT_TIMEOUT = "ENDPOINT_TIMEOUT"

@dataclass
class FulfillmentSessionEndedRequestError:
    type: SessionEndedErrorType
    message: str

@dataclass
class FulfillmentSessionEndedRequest(FulfillmentRequest):
    reason: SessionEndedReason
    error: FulfillmentSessionEndedRequestError = None

class CanFulfill(Enum):
    YES = "YES"
    NO = "NO"
    MAYBE = "MAYBE"

@dataclass
class FulfillmentCanFulfillIntentRequest:
    canFulfill: CanFulfill
    slots: dict # TODO: model

#
# Main request body
#

@dataclass
class FulfillmentBody:
    version: str
    session: FulfillmentSession
    context: FulfillmentContext
    request: Union[
        FulfillmentCanFulfillIntentRequest,
        FulfillmentSessionEndedRequest,
        FulfillmentIntentRequest,
        FulfillmentLaunchRequest
    ]

def from_dict(data: dict, data_class: type=FulfillmentBody):
    """
    Wraps :func:`dacite.from_dict` configuring enums for Alexa Fulfillment requests

    Args:
        data_class: The dataclass to use as schema
        data: Will be converted into a dataclass instance
    """    
    if data_class is FulfillmentBody:
        request_type = RequestType(data["request"]["type"])
       
        if request_type == RequestType.INTENT:
            request = from_dict(data["request"], data_class=FulfillmentIntentRequest)
        elif request_type == RequestType.LAUNCH:
            request = from_dict(data["request"], data_class=FulfillmentLaunchRequest)
        elif request_type == RequestType.SESSION_ENDED:
            request = from_dict(data["request"], data_class=FulfillmentSessionEndedRequest)
        elif request_type == RequestType.CAN_FULFILL_INTENT:
            request = from_dict(data["request"], data_class=FulfillmentCanFulfillIntentRequest)
            
        return FulfillmentBody(
            version=data["version"],
            session=from_dict(data["session"], data_class=FulfillmentSession),
            context=from_dict(data["context"], data_class=FulfillmentContext),
            request=request
        )

    return dacite.from_dict(
        data_class=data_class,
        data=data,
        config=dacite.Config(
            cast=[
                PlayerActivity,
                ViewportMode,
                ViewportShape,
                IntentConfirmationStatus,
                SlotType,
                SessionEndedReason,
                SessionEndedErrorType,
                RequestType
            ],
            type_hooks={
                datetime: lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%SZ')
            }
        )
    )