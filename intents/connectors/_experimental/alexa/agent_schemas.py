"""
An official Python implementation exists, which is more comprehensive, as well as more
complex: https://github.com/alexa/alexa-apis-for-python/blob/master/ask-smapi-model/ask_smapi_model/v1/skill/interaction_model/language_model.py
"""
from enum import Enum
from typing import List, Union
from dataclasses import dataclass, field

from intents.helpers.data_classes import OmitNone
from intents.connectors._experimental.alexa.slot_types import SystemSlotTypes

#
# Language Model
#

@dataclass
class LanguageModelIntentSlotMultipleValues:
    enabled: bool

@dataclass
class LanguageModelIntentSlot:
    name: str
    type: Union[SystemSlotTypes, str]
    samples: List[str] = OmitNone() # TODO: check
    multipleValues: LanguageModelIntentSlotMultipleValues = OmitNone()

@dataclass
class LanguageModelIntent:
    name: str
    slots: List[LanguageModelIntentSlot] = field(default_factory=list)
    samples: List[str] = field(default_factory=list)

@dataclass
class LanguageModelTypeValueName:
    value: str
    synonyms: List[str] = OmitNone()

@dataclass
class LanguageModelTypeValue:
    id: str
    name: LanguageModelTypeValueName

@dataclass
class LanguageModelType:
    name: str
    values: List[LanguageModelTypeValue]
    # TODO: valueSupplier

class FallbackIntentSensitivity(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

@dataclass
class LanguageModelConfigurationFallbackSensitivity:
    level: FallbackIntentSensitivity = FallbackIntentSensitivity.LOW

@dataclass
class LanguageModelConfiguration:
    fallbackIntentSensitivity: LanguageModelConfigurationFallbackSensitivity = OmitNone()

@dataclass
class LanguageModel:
    invocationName: str
    intents: List[LanguageModelIntent]
    types: List[LanguageModelType] = field(default_factory=list)
    modelConfiguration: LanguageModelConfiguration = OmitNone()

#
# Dialog
#

@dataclass
class Dialog:
    pass

#
# Prompts
#

@dataclass
class Prompt:
    pass

#
# Root
#

@dataclass
class InteractionModel:
    languageModel: LanguageModel
    dialog: Dialog = OmitNone()
    prompts: List[Prompt] = OmitNone()

@dataclass
class Agent:
    interactionModel: InteractionModel
    # TODO: complete
