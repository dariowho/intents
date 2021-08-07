import logging
from dataclasses import asdict
from typing import List, Dict
from collections import ChainMap

from intents.helpers.data_classes import custom_asdict_factory
from intents.model.intent import _IntentMetaclass
from intents.model.entity import _EntityMetaclass
from intents.language import intent_language, entity_language
from intents.language import agent_supported_languages, LanguageCode
from intents.connectors._experimental.snips import SnipsConnector
from intents.connectors._experimental.snips import entities as snips_entities
from intents.connectors._experimental.snips import agent_format as af

logger = logging.getLogger(__name__)

def render(connector: SnipsConnector) -> Dict[LanguageCode, dict]:
    languages: List[LanguageCode] = agent_supported_languages(connector.agent_cls)
    result = {}
    for lang in languages:
        try:
            rendered = render_dataset(connector, lang)
            result[lang] = asdict(rendered, dict_factory=custom_asdict_factory())
        except NotImplementedError as exc:
            logger.error("Could not export Agent for language %s: %s", lang, exc)
    return result

def render_dataset(connector: SnipsConnector, lang: LanguageCode) -> af.Dataset:
    return af.Dataset(
        intents={i.name: render_intent(connector, i, lang) for i in connector.agent_cls.intents},
        entities=render_all_entities(connector, lang),
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
    for param_metadata in intent_cls.parameter_schema.values():
        if param_metadata.is_list:
            raise NotImplementedError(f"Parameter '{param_metadata.name}' in Intent '{intent_cls}' "
                                      "is defined as List, but Snips NLU doesn't support list "
                                      "parameters.")
    for utterance in language_data.example_utterances:
        utterance_data = []
        for chunk in utterance.chunks():
            if isinstance(chunk, intent_language.TextUtteranceChunk):
                utterance_data.append(af.DatasetIntentUtteranceTextSegment(chunk.text))
            elif isinstance(chunk, intent_language.EntityUtteranceChunk):
                chunk: intent_language.EntityUtteranceChunk
                entity_name = connector._entity_service_name(chunk.entity_cls)
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

def render_all_entities(
    connector: SnipsConnector,
    lang: LanguageCode
) -> Dict[str, af.DatasetEntity]:
    """
    Render all entities in Agent. These are of three types:

    * System entities with builtin support by Snips
    * System entities that are unsupported by Snips
        * Patched with builtin entities by *Intents*
        * Can't be patched, but can be replaced by a placeholder entity
        * Can't be patched or replaced -> NotImplementedError
    * Custom entities
    """
    result = {}
    referenced_sys_entities = connector.agent_cls._referenced_sys_entities

    # Custom Entities
    entities = connector.agent_cls._entities_by_name.values()
    result.update(ChainMap(*[render_entity(connector, e, lang) for e in entities]))

    # Snips-supported Sys entities
    builtin_entities = [e for e in snips_entities.BUILTIN_ENTITIES]
    builtin_entities = [e for e in builtin_entities if e in referenced_sys_entities]
    for e in builtin_entities:
        if not connector.entity_mappings.is_mapped(e, lang):
            raise NotImplementedError(f"Agent references System Entity '{e}', but that is not "
                                      f"supported by Snips NLU for language '{lang}'")
    result.update({connector._entity_service_name(e): {} for e in builtin_entities})

    # Patched Sys entities
    patched_mappings = [m for m in snips_entities.PATCHED_MAPPINGS]
    patched_mappings = [m for m in patched_mappings if m.entity_cls in referenced_sys_entities]
    if patched_mappings:
        logger.warning("[%s] The following entities are referenced by Agent, but are not supported natively by Snips: "
                       "%s. They have been patched with Intents builtin entities, which may not provide the "
                       "same quality as native service entities.", lang, [m.entity_cls.name for m in patched_mappings])
        result.update(ChainMap(*[render_entity(connector, m.builtin_entity, lang) for m in patched_mappings]))

    # Placeholder entities
    placeholder_entities = [e for e in snips_entities.PLACEHOLDER_ENTITIES]
    placeholder_entities = [e for e in placeholder_entities if e in referenced_sys_entities]
    if placeholder_entities:
        logger.warning("[%s] The following entities are referenced by Agent, but are not supported natively by Snips: "
                       "%s. They have been replaced with empty placeholder entities, which is likely to lead to poor "
                       "prediction quality.", lang, [e.name for e in placeholder_entities])
    result.update(ChainMap(*[render_placeholder_entity(connector, e) for e in placeholder_entities]))



    return result

def render_entity(
    connector: SnipsConnector,
    entity_cls: _EntityMetaclass,
    lang: LanguageCode
) -> Dict[str, af.DatasetEntity]:
    language_data = entity_language.entity_language_data(connector.agent_cls, entity_cls, lang)
    language_data = language_data[lang]
    entries = []
    for e in language_data:
        entries.append(af.DatasetEntityEntry(value=e.value, synonyms=e.synonyms))
    
    service_name = connector._entity_service_name(entity_cls)
    return {
        service_name: af.DatasetEntity(
            data=entries,
            use_synonyms=True,
            automatically_extensible=True,
            matching_strictness=1.0
        )
    }

def render_placeholder_entity(
    connector: SnipsConnector,
    entity_cls: str,
):
    service_name = connector._entity_service_name(entity_cls)
    return {
        service_name: af.DatasetEntity(
            use_synonyms=True,
            automatically_extensible=True,
            matching_strictness=1.0,
            data=[]
        )
    }

# from intents.helpers.coffee_agent import CoffeeAgent
# from intents.connectors._experimental.snips import SnipsConnector
# snips = SnipsConnector(CoffeeAgent)
# render(snips)
