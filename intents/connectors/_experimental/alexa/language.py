"""
Alexa has peculiar requirements about language. Here we convert language data in
a format that Alexa can digest.
"""
import re
from typing import Dict, List
from dataclasses import dataclass

from intents import LanguageCode
from intents.types import AgentType, EntityType
from intents.language import entity_language

@dataclass
class AlexaEntityEntry(entity_language.EntityEntry):
    """
    Not all entity entry values/synonyms can be exported to Alexa: those which
    are not acceptable are must be stripped from result. Here we save
    Alexa-acceptable values in two additional fields.
    """
    alexa_value: str = None
    alexa_synonyms: List[str] = None

class AlexaLanguageComponent:

    agent_cls: AgentType

    _entry_id_to_value: Dict[LanguageCode, Dict[str, str]]

    def __init__(self, agent_cls: AgentType):
        self.agent_cls = agent_cls
        self._alexa_entry_to_value = {}

    def _build_indices(self, agent_cls: AgentType):
        # TODO: optimize (this loads all language data for entities)
        for entity_cls in agent_cls._entities_by_name.values():
            language_data = self.entity_language_data(agent_cls, entity_cls)
            for language, entries in language_data.values():
                entries_to_value = {}
                for entry in entries:
                    entries_to_value[entry.alexa_value] = entry.value
                self._alexa_entry_to_value[language] = entries_to_value


    def alexa_entry_id_to_value(self, alexa_entry_id: str, lang: LanguageCode) -> str:
        """
        Alexa returns an entry ID for each custom entry match. We define entry
        IDs in export, and here we translate them back to the original entry
        value, which is typically needed in prediction.

        Note that the entry value that Alexa knows may be different from the
        "canonical" value that is defined in language files. This is because
        some values/synonyms cannot be exported to Alexa. For instance, let's
        consider the :class:`CalculatorOperator` entity, with the following
        language data:

        .. code-block:: yaml

            entries:
                "*":
                    - times
                    - multiplied by
                    - product
                "+":
                    - plus
                    - addition
                ...

        Here `*` is not a valid value for Alexa. So we'll use the first viable
        synonim (`"times"`, which will produce an entry id like
        `"CalculatorOperator-times"`) as main value for Alexa, and the remaining
        ones as synonyms (`["multiplied by", "product"]`). However, we want to
        get back the original `*` to caller during inference, and this is what
        this method does:

        >>> lc.alexa_entry_id_to_value("CalculatorOperator-times", LanguageCode.ENGLISH)
        "*"
        """
        return self._entry_id_to_value[lang][alexa_entry_id]

    @staticmethod
    def entity_language_data(
        agent_cls: AgentType,
        entity_cls: EntityType,
        lang: LanguageCode=None
    ) -> Dict[LanguageCode, List[AlexaEntityEntry]]:
        """
        Load Entity language data, removing values and synonyms that can't be
        exported to Alexa.
        """
        result = {}
        language_data = entity_language.entity_language_data(agent_cls, entity_cls, lang)
        for language_code, entries in language_data.items():
            alexa_entries = []
            for entry in entries:
                all_values = [entry.value] + entry.synonyms
                acceptable_values = [v for v in all_values if _is_valid_entity_value(v)]
                if not acceptable_values:
                    raise ValueError(f"Entry {entry} of custom entity {entity_cls} has no valid values for "
                                     "Alexa. Please include at leas one standard alphanumeric synonym")
                alexa_entries.append(AlexaEntityEntry(
                    value=entry.value,
                    synonyms=entry.synonyms,
                    alexa_value=acceptable_values[0],
                    alexa_synonyms=acceptable_values[1:]
                ))
            result[language_code] = alexa_entries
        return result

    @staticmethod
    def entity_value_id(entity_cls: EntityType, entity_value: str):
        """
        Entity entries in Alexa have IDs. This is a centralized function to
        compute them.
        """
        return entity_cls.name + entity_value.replace(" ", "") # TODO: refine


def _is_valid_entity_value(val: str):
    # TODO: refine
    return bool(re.match(r'^[a-zA-Z0-9\s]+$', val))
