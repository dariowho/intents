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
from dataclasses import dataclass
from unittest.mock import patch

from intents import Agent, Intent, follow, LanguageCode
from intents.language.intent_language import IntentLanguageData, ExampleUtterance, IntentResponseGroup, TextIntentResponse

def mock_language_data(intent_cls: type, utterance: str, response: str="Any response"):
    
    return {
        LanguageCode.ENGLISH: IntentLanguageData(
            example_utterances=[ExampleUtterance(utterance, intent_cls)],
            slot_filling_prompts=None,
            responses={
                IntentResponseGroup.DEFAULT: [TextIntentResponse(choices=response)]
            }
        )
    }

@dataclass
class AskCoffee(Intent):
    """I'd like a coffee"""
    name = "testing.AskCoffee"
AskCoffee.__intent_language_data__ = mock_language_data(AskCoffee, "I'd like a coffee")

@dataclass
class AskEspresso(AskCoffee):
    """I'd like an espresso."""
    name = "testing.AskEspresso"
AskEspresso.__intent_language_data__ = mock_language_data(AskEspresso, "I'd like an espresso")
    
@dataclass
class AddMilk(Intent):
    """With milk please"""    
    parent_ask_coffee: AskCoffee = follow()
    name = "testing.AddMilk"
AddMilk.__intent_language_data__ = mock_language_data(AddMilk, "With milk please")

@dataclass
class AddSkimmedMilk(AddMilk):
    """With skimmed milk please"""    
    parent_ask_coffee: AskCoffee = follow()
    name = "testing.AddSkimmedMilk"
AddSkimmedMilk.__intent_language_data__ = mock_language_data(AddMilk, "With skimmed milk please")

@dataclass
class AndNoFoam(Intent):
    """And no foam"""    
    parent_add_milk: AddMilk = follow()
    name = "testing.AndNoFoam"
AndNoFoam.__intent_language_data__ = mock_language_data(AddMilk, "And no foam")

class CoffeeAgent(Agent):
    languages = ['en']

CoffeeAgent.register(AskCoffee)
CoffeeAgent.register(AskEspresso)
CoffeeAgent.register(AddMilk)
CoffeeAgent.register(AddSkimmedMilk)
CoffeeAgent.register(AndNoFoam)
