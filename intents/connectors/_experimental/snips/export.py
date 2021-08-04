from dataclasses import asdict
from typing import List, Dict

from intents.helpers.data_classes import custom_asdict_factory
from intents.model.intent import _IntentMetaclass
from intents.model.entity import _EntityMetaclass
from intents.language import intent_language, entity_language
from intents.language import agent_supported_languages, LanguageCode
from intents.service_connector import PatchedEntityMapping
from intents.connectors._experimental.snips import SnipsConnector
from intents.connectors._experimental.snips import entities as snips_entities
from intents.connectors._experimental.snips import agent_format as af

def render(connector: SnipsConnector) -> Dict[LanguageCode, dict]:
    languages: List[LanguageCode] = agent_supported_languages(connector.agent_cls)
    result = {}
    for lang in languages:
        rendered = render_dataset(connector, lang)
        result[lang] = asdict(rendered, dict_factory=custom_asdict_factory())
    return result

def render_dataset(connector: SnipsConnector, lang: LanguageCode) -> af.Dataset:
    entities = {e.name: render_entity(connector, e, lang) for e in connector.agent_cls._entities_by_name.values()}
    # TODO: only render those that are actually used in Agent
    all_patched_entities = [m.builtin_entity for m in connector.entity_mappings.values() if isinstance(m, PatchedEntityMapping)]
    entities.update({e.name: render_entity(connector, e, lang) for e in all_patched_entities})
    all_builtin_entities = [e.value for e in snips_entities.BuiltinEntityTypes]
    entities.update({e: {} for e in all_builtin_entities})
    return af.Dataset(
        intents={i.name: render_intent(connector, i, lang) for i in connector.agent_cls.intents},
        entities=entities,
        language=lang.value
    )

def render_intent(
    connector: SnipsConnector,
    intent_cls: _IntentMetaclass,
    lang: LanguageCode
) -> af.DatasetIntent:
    language_data = intent_language.intent_language_data(connector.agent_cls, intent_cls, lang)
    language_data = language_data[lang]
    utterances = []
    for utterance in language_data.example_utterances:
        utterance_data = []
        for chunk in utterance.chunks():
            if isinstance(chunk, intent_language.TextUtteranceChunk):
                utterance_data.append(af.DatasetIntentUtteranceTextSegment(chunk.text))
            elif isinstance(chunk, intent_language.EntityUtteranceChunk):
                chunk: intent_language.EntityUtteranceChunk
                mapping = connector.entity_mappings.get(chunk.entity_cls)
                entity_name = mapping.service_name if mapping else chunk.entity_cls.name
                utterance_data.append(af.DatasetIntentUtteranceEntitySegment(
                    text=chunk.parameter_value,
                    entity=entity_name,
                    slot_name=chunk.parameter_name
                ))
            else:
                raise ValueError(f"Unsupported utterance chunk type {type(chunk)}. This looks like a bug, please file an issue at https://github.com/dariowho/intents")
        utterances.append(af.DatasetIntentUtterance(
            data=utterance_data
        ))
    return af.DatasetIntent(
        utterances=utterances
    )

def render_entity(
    connector: SnipsConnector,
    entity_cls: _EntityMetaclass,
    lang: LanguageCode
) -> af.DatasetEntity:
    language_data = entity_language.entity_language_data(connector.agent_cls, entity_cls, lang)
    language_data = language_data[lang]
    entries = []
    for e in language_data:
        entries.append(af.DatasetEntityEntry(value=e.value, synonyms=e.synonyms))
        
    return af.DatasetEntity(
        data=entries,
        use_synonyms=False,
        automatically_extensible=False,
        matching_strictness=1.0
    )

# from intents.helpers.coffee_agent import CoffeeAgent
# from intents.connectors._experimental.snips import SnipsConnector
# snips = SnipsConnector(CoffeeAgent)
# render(snips)
