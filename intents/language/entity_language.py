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
from dataclasses import dataclass
from typing import List, Dict, Union

import yaml

# pylint: disable=unused-import
import intents # (needed for building docs)
from intents import LanguageCode
from intents.model.entity import EntityType
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

def make_language_data(entries: List[Union[str, List[str]]]) -> List[EntityEntry]:
    """
    Synthesize entity language data for an Entity from a list of entries. Each
    entry can just be a string, or a list where the first element is the value,
    and the remaining ones are synonyms.

    This function is mostly for internal use: it is recommended that you store
    language data in YAML files instead.

    Args:
        entries: A list of entity entries to build language data
    """
    result = []
    for e in entries:
        assert e
        if isinstance(e, str):
            e = [e]
        result.append(EntityEntry(value=e[0], synonyms=e[1:]))
    return result

def entity_language_data(
    agent_cls: "intents.model.agent.AgentType",
    entity_cls: EntityType,
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
        # TODO: validate custom language data
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
