"""
Utilities to manage the Agent's language resources. An Agent is defined as a
Python package. The package is expected to have a `language` folder at its top
level, containing language resources for intents and entities, in the for of
YAML files.

.. warning::

    Documentation about language format is being written and currently is not
    available. The best option at the moment is to look at language resources for
    the example agent at https://github.com/dariowho/intents/tree/master/example_agent/language.
"""
from intents.language.language_codes import LanguageCode, LANGUAGE_CODES
from intents.language.agent_language import agent_language_folder, agent_supported_languages
from intents.language.intent_language import intent_language_data, IntentResponseGroup, IntentResponse, TextIntentResponse, ImageIntentResponse, QuickRepliesIntentResponse, CardIntentResponse, CustomPayloadIntentResponse, IntentLanguageData, ExampleUtterance, UtteranceChunk, TextUtteranceChunk, EntityUtteranceChunk
from intents.language.entity_language import entity_language_data, EntityEntry

# from example_agent import ExampleAgent
# from example_agent import smalltalk

# examples, responses = intent_language_data(ExampleAgent, smalltalk.user_name_give)
# for e in examples:
#     print(e.chunks())

# from example_agent import ExampleAgent
# from example_agent.restaurant import PizzaType

# entity_language_data(ExampleAgent, PizzaType)
