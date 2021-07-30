"""
Each of your Entity classes is supposed to define language data in a
`language/<LANGUAGE-CODE>/ENTITY_MyEntityClass.yaml` YAML file.

An Entity language file simply contains a list of entries and their synonyms.
For instance, this is the content of `example_agent/language/en/ENTITY_PizzaType.yaml`:

.. code-block:: yaml

    entries:
      Margherita:
        - normal
        - standard
      Diavola:
        - spicy
        - pepperoni
      Capricciosa:
        - with olives and artichokes

Check out :mod:`example_agent.restaurant` for a hands-on example with custom entities.
"""
import os
from typing import List, Dict
from dataclasses import dataclass

import yaml

# pylint: disable=unused-import
import intents # (needed for building docs)
from intents.model.entity import _EntityMetaclass
from intents.language.language_codes import LanguageCode
from intents.language.agent_language import agent_language_folder

@dataclass
class EntityEntry:
    """
    Model Language entry for a Custom Entity. `EntityEntry` objects are produced
    by :func:`entity_language_data` as a result of parsing YAML language
    resources.
    
    Args:
        value: The canonical value of the entry (e.g. "Diavola")
        synonyms: A set of synonyms that refer to the same entry (e.g. "spicy",
            "pepperoni", ...)
    """
    value: str
    synonyms: List[str]

def entity_language_data(
    agent_cls: "intents.model.agent._AgentMetaclass",
    entity_cls: _EntityMetaclass,
    language_code: LanguageCode=None
) -> Dict[LanguageCode, List[EntityEntry]]:
    """
    Return language data for a given Entity.

    Args:
        agent_cls: The Agent class that registered the Entity
        entity_cls: The Entity class to load language resources for
        language_code: A specific Language to load. If not present, all
            available languages will be returned
    """
    # Custom language data
    if entity_cls.__entity_language_data__:
        # TODO: check custom language data
        if language_code:
            return {language_code: entity_cls.__entity_language_data__[language_code]}
        return entity_cls.__entity_language_data__
    
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
