import os
from typing import List, Dict
from dataclasses import dataclass

import yaml

from intents.model.entity import _EntityMetaclass
from intents.language.language_codes import LanguageCode
from intents.language.agent_language import agent_language_folder

@dataclass
class EntityEntry:

    value: str
    synonyms: List[str]

def entity_language_data(agent_cls: "agent._AgentMetaclass", entity_cls: _EntityMetaclass, language_code: LanguageCode=None) -> Dict[LanguageCode, List[EntityEntry]]:
    # Custom language data
    if entity_cls.custom_language_data:
        # TODO: check custom language data
        if language_code:
            return {language_code: entity_cls.custom_language_data[language_code]}
        else:
            return entity_cls.custom_language_data
    
    language_folder = agent_language_folder(agent_cls)

    if not language_code:
        result = {}
        for language_code in agent_cls.languages:
            language_data = entity_language_data(agent_cls, entity_cls, language_code)
            result[language_code] = language_data[language_code]
        return result

    language_file = os.path.join(language_folder, language_code.value, f"ENTITY_{entity_cls.name}.yaml")
    if not os.path.isfile(language_file):
        raise ValueError(f"Language file not found for entity '{entity_cls.name}'. Expected path: {language_file}.")

    with open(language_file, 'r') as f:
        language_data = yaml.load(f.read(), Loader=yaml.FullLoader)

    if not language_data:
        return []

    entries_data = language_data.get('entries', [])
    if not isinstance(entries_data, dict):
        raise ValueError(f"Invalid Entity language data for entity {entity_cls.name}. Entries data must be a dict. Entries data: {entries_data}")

    entries = []
    for value, synonyms in entries_data.items():
        if not isinstance(synonyms, list):
            raise ValueError(f"Invalid language data for entry {entity_cls.name}. Synonims data must always be lists. Synonims data for '{value}': '{synonyms}'")
        entries.append(EntityEntry(value, synonyms))

    return {language_code: entries}
