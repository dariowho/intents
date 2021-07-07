"""
Features:

- [OK] intent
- [OK] example utterances
- [  ] example utterances with parameter references
- [  ] system entity slots
- [  ] custom entity slots
- [  ] input/output contexts
- [OK] multi language
"""

from typing import List, Dict
from dataclasses import asdict

from intents import Intent
from intents.language import intent_language_data, agent_supported_languages, LanguageCode
from intents.connectors.alexa import agent_schemas as ask_schema
from intents.helpers import custom_asdict_factory

def render(connector: "AlexaConnector") -> Dict[LanguageCode, dict]:
    languages: List[LanguageCode] = agent_supported_languages(connector.agent_cls)
    result = {}
    for lang in languages:
        rendered = render_agent(connector, lang)
        result[lang] = asdict(rendered, dict_factory=custom_asdict_factory())
    return result

def render_agent(connector: "AlexaConnector", lang: LanguageCode) -> ask_schema.Agent:
    return ask_schema.Agent(
        interactionModel=render_interaction_model(connector, lang)
    )

def render_interaction_model(connector: "AlexaConnector", lang: LanguageCode) -> ask_schema.InteractionModel:
    return ask_schema.InteractionModel(
        languageModel=render_language_model(connector, lang)
    )

def render_language_model(connector: "AlexaConnector", lang: LanguageCode) -> ask_schema.LanguageModel:
    return ask_schema.LanguageModel(
        invocationName=connector.invocation_name,
        intents=[render_intent(i, connector, lang) for i in connector.agent_cls.intents]
        # TODO: complete
    )

def render_intent(intent_cls: type(Intent), connector: "AlexaConnector", lang: LanguageCode) -> ask_schema.LanguageModelIntent:
    return ask_schema.LanguageModelIntent(
        name=intent_cls.name,
        samples=render_intent_samples(intent_cls, connector, lang)
        # TODO: complete
    )

def render_intent_samples(intent_cls: type(Intent), connector: "AlexaConnector", lang: LanguageCode) -> List[str]:
    language_data = intent_language_data(connector.agent_cls, intent_cls, lang)
    language_data = language_data[lang]
    result = []
    for utterance in language_data.example_utterances:
        # TODO: render slot references
        result.append(str(utterance))
    return result

# from example_agent.agent import ExampleAgent
# from intents.connectors.alexa import AlexaConnector

# alexa = AlexaConnector(ExampleAgent, "any invocation")
# # render(alexa)

# alexa.export("TMP_ALEXA.json")