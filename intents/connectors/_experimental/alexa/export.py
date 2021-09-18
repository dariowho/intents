"""
Features:

- [OK] intent
- [OK] example utterances
- [OK] example utterances with parameter references
- [OK] system entity slots
- [OK] custom entity slots
- [  ] plain text responses
- [  ] intent relations
- [OK] multi language

Note that there are some relevant TODOs in this module (e.g. intent names may be
ambiguous, punctuation is stripped from utterances, and so on..)
"""
import re
import logging
from typing import List, Dict, Type
from dataclasses import asdict

from intents import Intent, Agent, EntityMixin
from intents.language import intent_language, intent_language_data, agent_supported_languages, LanguageCode
from intents.connectors._experimental.alexa import agent_schemas as ask_schema
from intents.connectors._experimental.alexa import names, language

from intents.helpers.data_classes import custom_asdict_factory

logger = logging.getLogger(__name__)

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
    ),
    ask_schema.LanguageModelIntent(
        name="AMAZON.FallbackIntent",
        samples=[]
    )
]

class AlexaExportComponent:
    agent_cls: Type[Agent]
    names_component: names.AlexaNamesComponent
    language_component: language.AlexaLanguageComponent
    invocation_name: str

    def __init__(self,
        agent_cls: Type[Agent],
        names_component: names.AlexaNamesComponent,
        language_component: language.AlexaLanguageComponent,
        invocation_name: str
    ):
        self.agent_cls = agent_cls
        self.names_component = names_component
        self.language_component = language_component
        self.invocation_name = invocation_name

    def render(self) -> Dict[LanguageCode, dict]:
        languages: List[LanguageCode] = agent_supported_languages(self.agent_cls)
        result = {}
        for lang in languages:
            rendered = self.render_agent(lang)
            rendered.interactionModel.languageModel.intents.extend(DEFAULT_INTENTS)
            result[lang] = asdict(rendered, dict_factory=custom_asdict_factory())
        return result

    def render_agent(self, lang: LanguageCode) -> ask_schema.Agent:
        return ask_schema.Agent(
            interactionModel=self.render_interaction_model(lang)
        )

    def render_interaction_model(self, lang: LanguageCode) -> ask_schema.InteractionModel:
        return ask_schema.InteractionModel(
            languageModel=self.render_language_model(lang)
        )

    def render_language_model(self, lang: LanguageCode) -> ask_schema.LanguageModel:
        intents = [self.render_intent(i, lang) for i in self.agent_cls.intents]
        intents = [i for i in intents if i]
        return ask_schema.LanguageModel(
            invocationName=self.invocation_name,
            intents=intents,
            types=[self.render_slot_type(e, lang) for e in self.agent_cls._entities_by_name.values()]
            # TODO: complete
        )

    #
    # Intent
    #

    def render_intent(self, intent_cls: Type[Intent], lang: LanguageCode) -> ask_schema.LanguageModelIntent:
        """
        Return None if intent has no example utterances
        """
        slots = self.render_intent_slots(intent_cls)
        samples = self.render_intent_samples(intent_cls, lang)
        if not samples:
            return None
        return ask_schema.LanguageModelIntent(
            name=self.names_component.intent_to_alexa(intent_cls),
            slots=slots,
            samples=samples
            # TODO: complete
        )

    def render_intent_slots(self, intent_cls: Type[Intent]) -> List[ask_schema.LanguageModelIntentSlot]:
        result = []
        for param_name, param_metadata in intent_cls.parameter_schema.items():
            entity_cls = param_metadata.entity_cls
            slot_type = self.names_component.entity_service_name(entity_cls)

            result.append(ask_schema.LanguageModelIntentSlot(
                name=param_name,
                type=slot_type,
                multipleValues=ask_schema.LanguageModelIntentSlotMultipleValues(
                    enabled=param_metadata.is_list
                )
            ))
        return result


    def render_intent_samples(self, intent_cls: Type[Intent], lang: LanguageCode) -> List[str]:
        language_data = intent_language_data(self.agent_cls, intent_cls, lang)
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
            utterance = re.sub(r"[^a-zA-Z0-9 \-\{\}\_\.\']+", '', utterance)
            result.append(utterance)
        return result

    #
    # Slot Type
    #

    def render_slot_type(self, entity_cls: Type[EntityMixin], lang: LanguageCode) -> ask_schema.LanguageModelType:
        language_data = self.language_component.entity_language_data(entity_cls, lang)
        language_data = language_data[lang]
        slot_values = [self.render_slot_value(entity_cls, entry) for entry in language_data]
        slot_values = [v for v in slot_values if v]
        return ask_schema.LanguageModelType(
            name=entity_cls.name,
            values=slot_values
        )

    def render_slot_value(self, entity_cls: Type[EntityMixin], entity_entry: language.AlexaEntityEntry) -> ask_schema.LanguageModelTypeValue:
        return ask_schema.LanguageModelTypeValue(
            id=self.language_component.entry_value_id(entity_cls, entity_entry),
            name=ask_schema.LanguageModelTypeValueName(
                value=entity_entry.alexa_value,
                synonyms=entity_entry.alexa_synonyms
            )
        )

# from example_agent.agent import ExampleAgent
# from intents.connectors._experimental.alexa import AlexaConnector

# alexa = AlexaConnector(ExampleAgent, "any invocation")
# # render(alexa)

# alexa.export("./TMP_ALEXA")