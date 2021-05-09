"""
Here we model the JSON format of Lex agents with Python dataclasses.

We consider Lex schema version 1.0, as it is defined in
https://docs.aws.amazon.com/lex/latest/dg/import-export-format.html.

TODO: These models are not tested
"""
from dataclasses import dataclass, field
from typing import List, Union

#
# Generic
#

@dataclass
class Message:
    content: str
    contentType: str = "PlainText" # PlainText or SSML or CustomPayload

#
# Slot Types (custom Entities)
#

@dataclass
class SlotTypeEnumerationValue:
    value: str

@dataclass
class SlotTypeEnumerationValueWithSynonims(SlotTypeEnumerationValue):
    synonims: List[str]

@dataclass
class SlotType:
    name: str
    version: str = "1"
    description: str = ""
    enumerationValues: List[SlotTypeEnumerationValue]
    valueSelectionStrategy: str = "ORIGINAL_VALUE" # ORIGINAL_VALUE or TOP_RESOLUTION
    
# TODO: slot types that extend system types (i.e. regex)

#
# Intents
#

@dataclass
class IntentFulfillmentActivity:
    type: str = "ReturnIntent" # ReturnIntent or CodeHook

@dataclass
class IntentSlotValueElicitationPrompt:
    messages: List[Message]
    maxAttempts: int = 2

@dataclass
class IntentConclusionStatementMessage(Message):
    groupNumber: int = 1

@dataclass
class IntentConclusionStatement:
    """
    The Intent responses
    """
    messages: List[IntentConclusionStatementMessage]

@dataclass
class IntentSlot:
    name: str
    slotType: str
    description: str = ""
    slotConstraint: str = "Optional" # Optional or Required
    valueElicitationPrompt: IntentSlotValueElicitationPrompt = None # TODO: required for required parameters. Check with Optional
    priority: int = 2
    sampleUtterances: List[str]

@dataclass
class Intent:
    """
    https://docs.aws.amazon.com/lex/latest/dg/API_PutIntent.html
    """
    name: str
    version: str = "1"
    description: str = ""
    # TODO: confirmation prompts (confirmationPrompt + rejectionStatement) ->
    # implement equivalent in Dialogflow
    fulfillmentActivity: IntentFulfillmentActivity = field(default_factory=IntentFulfillmentActivity)
    sampleUtterances: List[str] = field(default_factory=list)
    slots: List
    conclusionStatement: IntentConclusionStatement = None # TODO: check if key has to be removed altogether when None
    # TODO: standalone intents also have slotTypes

#
# Bot (Agent)
#

@dataclass
class BotClarificationPrompt:
    messages: List[Message]
    maxAttempts: int = 2

@dataclass
class BotAbortStatement:
    messages: List[Message]

@dataclass
class Bot:
    name: str
    clarificationPrompt: BotClarificationPrompt
    abortStatement: BotAbortStatement
    version: str = "1"
    description: str = ""
    nluIntentConfidenceThreshold: float = 0.4
    detectSentiment: bool = False
    enableModelImprovements: bool = True
    intents: List[Intent] = field(default_factory=list)
    slotTypes: List[SlotType] = field(default_factory=list)
    voiceId: str = "Salli"
    childDirected: bool = False
    locale: str = "en-US"
    idleSessionTTLInSeconds: int = 600

#
# Standalone Resource
#

@dataclass
class ResourceMetadata:
    """
    This is used when exporting standalone Intents, Slot Types or whole Agents.
    """
    schemaVersion: str = "1.0"
    importType: str = "LEX"
    importFormat: str = "JSON"

@dataclass
class StandaloneResource:
    """
    Intents, Slot Types or whole Agents can be exported as standalone resources
    """
    metadata: ResourceMetadata = field(default_factory=ResourceMetadata)
    resource: Union[SlotType]
