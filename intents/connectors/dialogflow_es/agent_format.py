"""
Here we define classes that marshal the output format of Dialogflow Agents. We use
these to generate a set of JSON files representing the agent, in a format that is compatible
with the ones you get from Settings > Export in the Dialogflow console.

A Dialogflow Agent is represented by a compressed folder that contains the Agent
metadata, a set of Intents and a set of Entities.

Agent **metadata** are stored in a `agent.json` file. A complementary
`package.json` contains a standard `{"version": "1.0.0"}`. TODO: model metadata.

Intents can be found in the `intents/` folder. Each **intent** is defined by 2 files:

* `intents/<INTENT_NAME>.json` contains the Intent definition. This is modelled in :class:`Intent`
* `intents/<INTENT_NAME>_usersays.json` contains the list of example utterances. Each
  utterance is modelled in :class:`IntentUsersays`

Intents are modelled in the official client as Protobuf structures
(https://cloud.google.com/dialogflow/es/docs/reference/rpc/google.cloud.dialogflow.v2beta1#intent);
however, they seem to have little in common with the JSON output format.

Entities can be found in the `entities/` folder. Each **entity** is defined by 2
files:

* `entities/<ENTITY_NAME>.json` contains the Entity definition, this is modelled
  in :class:`Entity`
* `entities/<ENTITY_NAME>_entries.json` contains the entity values and their synonyms
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Union, Dict

#
# agent.json
#

@dataclass
class AgentGoogleAssistantOauthLinking:
    required: bool = False
    providerId: str = ""
    authorizationUrl: str = ""
    tokenUrl: str = ""
    scopes: str = ""
    privacyPolicyUrl: str = ""
    grantType: str = "AUTH_CODE_GRANT"

@dataclass
class AgentGoogleAssistant:
    project: str
    oAuthLinking: AgentGoogleAssistantOauthLinking
    googleAssistantCompatible: bool = False
    welcomeIntentSignInRequired: bool = False
    startIntents: List = field(default_factory=list)
    systemIntents: List = field(default_factory=list)
    endIntentIds: List = field(default_factory=list)
    voiceType: str = "MALE_1"
    capabilities: List = field(default_factory=list)
    env: str = ""
    protocolVersion: str = "V2"
    autoPreviewEnabled: bool = False
    isDeviceAgent: bool = False

@dataclass
class AgentWebhook:
    url: str = ""
    username: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    available: bool = False
    useForDomains: bool = False
    cloudFunctionsEnabled: bool = False
    cloudFunctionsInitialized: bool = False

@dataclass
class Agent:
    displayName: str
    webhook: AgentWebhook
    googleAssistant: AgentGoogleAssistant
    description: str = ""
    language: str = "en"
    shortDescription: str = ""
    examples: str = ""
    linkToDocs: str = ""
    disableInteractionLogs: bool = False
    disableStackdriverLogs: bool = True
    defaultTimezone: str = "Europe/Rome" # TODO: check
    isPrivate: bool = True
    mlMinConfidence: float = 0.3
    supportedLanguages: List[str] = field(default_factory=list)
    onePlatformApiVersion: str = "v2" # TODO: check
    secondaryKey: str = "" # TODO: check
    analyzeQueryTextSentiment: bool = False
    enabledKnowledgeBaseNames: List = field(default_factory=list)
    knowledgeServiceConfidenceAdjustment: float = -0.4
    dialogBuilderMode: bool = False
    baseActionPackagesUrl: str = ""

#
# entities/<ENTITY_NAME>.json
#

@dataclass
class Entity:
    id: str
    name: str
    isOverridable: bool = True
    isEnum: bool = False
    isRegexp: bool = False
    automatedExpansion: bool = False
    allowFuzzyExtraction: bool = False


#
# entities/<ENTITY_NAME>_entries_en.json
#

@dataclass
class EntityEntry:
    value: str
    synonyms: List[str]

#
# intents/<INTENT_NAME>.json
#

@dataclass
class AffectedContext:
    """
    This is the name of output contexts in the DF Intent definition
    """
    name: str
    lifespan: int

@dataclass
class Prompt:
    value: str
    lang: str

@dataclass
class Parameter:
    id: str
    name: str
    required: bool
    dataType: str
    value: str
    defaultValue: str = ""
    isList: bool = False
    prompts: List[Prompt] = field(default_factory=list)
    promptMessages: List = field(default_factory=list)
    noMatchPromptMessages: List = field(default_factory=list)
    noInputPromptMessages: List = field(default_factory=list)
    outputDialogContexts: List = field(default_factory=list)

class ResponseMessageTypes(Enum):
    TEXT = "0"
    CARD = "1"
    QUICK_REPLIES = "2"
    IMAGE = "3"
    CUSTOM = "4"

@dataclass
class ResponseMessage:
    lang: str
    type: str = "0" # TODO: use Enum with helpers.data_classes.custom_asdict_factory()
    title: str = ""
    textToSpeech: str = ""
    condition: str = ""
    platform: str = None # TODO: model different platforms


@dataclass
class TextResponseMessage(ResponseMessage):
    speech: List[str] = ""
    type: str = "0"   # TODO: use Enum with helpers.data_classes.custom_asdict_factory()

@dataclass
class QuickRepliesResponseMessage(ResponseMessage):
    replies: List[str] = field(default_factory=list)
    title: str = "Quick Replies"
    type: str = "2"   # TODO: use Enum with helpers.data_classes.custom_asdict_factory()

@dataclass
class ImageResponseMessage(ResponseMessage):
    imageUrl: str = ""
    title: str = ""
    type: str = "3"   # TODO: use Enum with helpers.data_classes.custom_asdict_factory()

@dataclass
class CardResponseMessageButton:
    text: str
    postback: str = None

@dataclass
class CardResponseMessage(ResponseMessage):
    title: str = ""
    subtitle: str = ""
    imageUrl: str = ""
    buttons: List[CardResponseMessageButton] = None
    type: str = "1"   # TODO: use Enum with helpers.data_classes.custom_asdict_factory()

@dataclass
class CustomPayloadResponseMessage(ResponseMessage):
    payload: Dict[str, dict] = field(default_factory=dict)
    type: str = "4"   # TODO: use Enum with helpers.data_classes.custom_asdict_factory()


@dataclass
class Response:
    affectedContexts: List[AffectedContext]
    parameters: List[Parameter]
    messages: List[ResponseMessage]
    speech: List = field(default_factory=list)
    resetContexts: bool = False
    action: str = ""

@dataclass
class Event:
    name: str

@dataclass
class Intent:
    id: str
    name: str
    responses: List[Response]
    auto: bool = True
    contexts: List[str] = field(default_factory=list)
    priority: int = 500000
    webhookUsed: bool = True
    webhookForSlotFilling: bool = True
    fallbackIntent: bool = False
    events: List[Event] = field(default_factory=list)
    conditionalResponses: List = field(default_factory=list)
    condition: str = ""
    conditionalFollowupEvents: List = field(default_factory=list)

#
# intents/<INTENT_NAME>_usersays.json
#

class UsersaysChunk:
    pass

@dataclass
class UsersaysEntityChunk(UsersaysChunk):
    text: str
    meta: str
    alias: str
    userDefined: bool


@dataclass
class UsersaysTextChunk(UsersaysChunk):
    text: str
    userDefined: bool


@dataclass
class IntentUsersays:
    id: str
    lang: str
    data: List[Union[UsersaysTextChunk, UsersaysEntityChunk]]
    isTemplate: bool = False
    count: int = 0
    updated: int = 0
