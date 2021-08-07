"""
This module contains :class:`CoffeeAgent`, a toy agent that is used for testing.
Testing agents may require recording requests and responses in hand-crafted
scenarios, and while Example Agent seems to fit the purpose, we avoid it for two
reasons:

* Some scenarios may be too peculiar to be included there
* A breaking change in the Agent would require generating all the service
  responses from scratch, as tests must match responses with the CoffeeAgent
  class. Example Agent is there for demonstration purposes, and it should be
  possible to update its definition at any time to better express the potential
  of *Intents*.
"""
from typing import Union, List
from dataclasses import dataclass
from unittest.mock import patch

from intents import Agent, Intent, Entity, follow, LanguageCode
from intents.language.intent_language import IntentLanguageData, ExampleUtterance, IntentResponseGroup, TextIntentResponse
from intents.language.entity_language import EntityEntry

def mock_language_data(
    intent_cls: type,
    utterances: Union[str, List[str]],
    responses: Union[str, List[str]]="Any response",
    language: LanguageCode = LanguageCode.ENGLISH
):
    if isinstance(utterances, str):
        utterances = [utterances]
    if isinstance(responses, str):
        responses = [responses]
    return {
        language: IntentLanguageData(
            example_utterances=[ExampleUtterance(u, intent_cls) for u in utterances],
            responses={
                IntentResponseGroup.DEFAULT: [TextIntentResponse(choices=responses)]
            }
        )
    }

class CoffeeRoast(Entity):
    __entity_language_data__ = {
        LanguageCode.ENGLISH: [
            EntityEntry("light", []),
            EntityEntry("medium", []),
            EntityEntry("dark", []),
        ]
    }

@dataclass
class AskCoffee(Intent):
    """I'd like a coffee"""
    name = "AskCoffee"
    roast: CoffeeRoast = "medium"
AskCoffee.__intent_language_data__ = mock_language_data(
    AskCoffee,
    ["I'd like a coffee", "I'd like a $roast{medium} roast coffee"],
    ["$roast roast coffee, good choice!", "Alright, $roast roasted coffee for you"]
)

@dataclass
class AskEspresso(AskCoffee):
    """I'd like an espresso."""
    name = "AskEspresso"
AskEspresso.__intent_language_data__ = mock_language_data(
    AskEspresso,
    ["I'd like an espresso", "I'd like a $roast{medium} roast espresso"],
    ["$roast roast espresso, good choice!", "Alright, $roast roasted espresso for you"]
)
    
@dataclass
class AddMilk(Intent):
    """With milk please"""    
    parent_ask_coffee: AskCoffee = follow()
    name = "AddMilk"
AddMilk.__intent_language_data__ = mock_language_data(AddMilk, "With milk please")

@dataclass
class AddSkimmedMilk(AddMilk):
    """With skimmed milk please"""    
    parent_ask_coffee: AskCoffee = follow()
    name = "AddSkimmedMilk"
AddSkimmedMilk.__intent_language_data__ = mock_language_data(AddMilk, "With skimmed milk please")

@dataclass
class AndNoFoam(Intent):
    """And no foam"""    
    parent_add_milk: AddMilk = follow()
    name = "AndNoFoam"
AndNoFoam.__intent_language_data__ = mock_language_data(AddMilk, "And no foam")

class CoffeeAgent(Agent):
    languages = ['en']

CoffeeAgent.register(AskCoffee)
CoffeeAgent.register(AskEspresso)
CoffeeAgent.register(AddMilk)
CoffeeAgent.register(AddSkimmedMilk)
CoffeeAgent.register(AndNoFoam)
