"""
Features:

- [OK] intent
- [OK] example utterances
- [OK] example utterances with parameter references
- [OK] system entity slots
- [  ] custom entity slots
- [  ] plain text responses
- [  ] input/output contexts
- [OK] multi language
"""
import re
from typing import List, Dict
from dataclasses import asdict

from intents import Intent
from intents.model.entity import Entity
from intents.language import intent_language, intent_language_data, entity_language, entity_language_data, agent_supported_languages, LanguageCode
from intents.connectors.alexa import agent_schemas as ask_schema
from intents.helpers import custom_asdict_factory

# TODO: model in framework
DEFAULT_INTENTS = [
    ask_schema.LanguageModelIntent(
        name="AMAZON.CancelIntent",
        samples=[]
    ),
    ask_schema.LanguageModelIntent(
        name="AMAZON.HelpIntent",
        samples=[]
    ),
    ask_schema.LanguageModelIntent(
        name="AMAZON.StopIntent",
        samples=[]
    ),
    ask_schema.LanguageModelIntent(
        name="AMAZON.NavigateHomeIntent",
        samples=[]
    )
]

def render(connector: "AlexaConnector") -> Dict[LanguageCode, dict]:
    languages: List[LanguageCode] = agent_supported_languages(connector.agent_cls)
    result = {}
    for lang in languages:
        rendered = render_agent(connector, lang)
        rendered.interactionModel.languageModel.intents.extend(DEFAULT_INTENTS)
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
        intents=[render_intent(i, connector, lang) for i in connector.agent_cls.intents],
        types=[render_slot_type(e, connector, lang) for e in connector.agent_cls._entities_by_name.values()]
        # TODO: complete
    )

#
# Intent
#

def render_intent(intent_cls: type(Intent), connector: "AlexaConnector", lang: LanguageCode) -> ask_schema.LanguageModelIntent:
    return ask_schema.LanguageModelIntent(
        name=intent_cls.name.replace(".", "_"), # TODO: find better policy: this may cause ambiguous names
        slots=render_intent_slots(intent_cls, connector),
        samples=render_intent_samples(intent_cls, connector, lang)
        # TODO: complete
    )

def render_intent_slots(intent_cls: type(Intent), connector: "AlexaConnector") -> List[ask_schema.LanguageModelIntentSlot]:
    result = []
    for param_name, param_metadata in intent_cls.parameter_schema().items():
        entity_cls = param_metadata.entity_cls
        slot_type = connector._entity_service_name(entity_cls)

        result.append(ask_schema.LanguageModelIntentSlot(
            name=param_name,
            type=slot_type,
            multipleValues=ask_schema.LanguageModelIntentSlotMultipleValues(
                enabled=param_metadata.is_list
            )
        ))
    return result


def render_intent_samples(intent_cls: type(Intent), connector: "AlexaConnector", lang: LanguageCode) -> List[str]:
    language_data = intent_language_data(connector.agent_cls, intent_cls, lang)
    language_data = language_data[lang]
    result = []
    for utterance in language_data.example_utterances:
        rendered_chunks = []
        for chunk in utterance.chunks():
            if isinstance(chunk, intent_language.TextUtteranceChunk):
                rendered_chunks.append(chunk.text)
            elif isinstance(chunk, intent_language.EntityUtteranceChunk):
                rendered_chunks.append("{" + chunk.parameter_name + "}")
            else:
                raise ValueError(f"Unsupported utterance chunk type {type(chunk)}. This looks like a bug, please file an issue at https://github.com/dariowho/intents")
        utterance = "".join(rendered_chunks)
        # TODO: refine, especially for List parameters. Also, "{", "}" and
        # "_" are only allowed in slot references
        utterance = re.sub(r"[^a-zA-Z \-\{\}\_\.\']+", '', utterance)
        result.append(utterance)
    return result

#
# Slot Type
#

def render_slot_type(entity_cls: type(Entity), connector: "AlexaConnector", lang: LanguageCode) -> ask_schema.LanguageModelType:
    language_data = entity_language_data(connector.agent_cls, entity_cls, lang)
    language_data = language_data[lang]
    return ask_schema.LanguageModelType(
        name=entity_cls.name,
        values=[render_slot_value(entity_cls, v, connector) for v in language_data]
    )

def render_slot_value(entity_cls: type(Entity), entity_entry: entity_language.EntityEntry, connector: "AlexaConnector") -> ask_schema.LanguageModelTypeValue:
    return ask_schema.LanguageModelTypeValue(
        id=connector.entity_value_id(entity_cls, entity_entry),
        name=ask_schema.LanguageModelTypeValueName(
            value=entity_entry.value,
            synonyms=entity_entry.synonyms
        )
    )

# from example_agent.agent import ExampleAgent
# from intents.connectors.alexa import AlexaConnector

# alexa = AlexaConnector(ExampleAgent, "any invocation")
# # render(alexa)

# alexa.export("TMP_ALEXA.json")