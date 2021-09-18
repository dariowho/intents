"""
Alexa has peculiar requirements about language. Here we convert language data in
a format that Alexa can digest.
"""
import re
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Type

from intents import EntityMixin, Agent, LanguageCode
from intents.language import entity_language, match_agent_language

LOCALE_MAP = {
    "ar-SA": None,
    "de-DE": LanguageCode.GERMAN,
    "en-AU": LanguageCode.ENGLISH,
    "en-CA": LanguageCode.ENGLISH_US,
    "en-GB": LanguageCode.ENGLISH_UK,
    "en-IN": LanguageCode.ENGLISH,
    "en-US": LanguageCode.ENGLISH_US,
    "es-ES": LanguageCode.SPANISH,
    "es-MX": LanguageCode.SPANISH_LATIN_AMERICA,
    "es-US": LanguageCode.SPANISH_LATIN_AMERICA,
    "fr-CA": LanguageCode.FRENCH,
    "fr-FR": LanguageCode.FRENCH,
    "hi-IN": None,
    "it-IT": LanguageCode.ITALIAN,
    "ja-JP": None,
    "pt-BR": None
}

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

    agent_cls: Type[Agent]

    _entry_id_to_value: Dict[LanguageCode, Dict[str, str]]

    def __init__(self, agent_cls: Type[Agent]):
        self.agent_cls = agent_cls
        self._entry_id_to_value = {}

        self._build_indices(agent_cls)

    def _build_indices(self, agent_cls: Type[Agent]):
        # TODO: optimize (this loads all language data for entities)
        self._entry_id_to_value = defaultdict(dict)
        for entity_cls in agent_cls._entities_by_name.values():
            language_data = self._entity_language_data(agent_cls, entity_cls)
            for language, entries in language_data.items():
                entries_to_value = {}
                for entry in entries:
                    value_id = self.entry_value_id(entity_cls, entry)
                    entries_to_value[value_id] = entry.value
                self._entry_id_to_value[language].update(entries_to_value)
        self._entry_id_to_value = dict(self._entry_id_to_value)

    def alexa_locale_to_agent_language(self, locale_str: str) -> LanguageCode:
        """
        Converts a Locale, as it comes in Alexa requests, to one of the
        languages that are supported by Agent. The following scenarios may
        happen:

        * Alexa locale is not supported by *Intents* (e.g. "ar-SA") ->
          :class:`KeyError`
        * Alexa locale is one of the Agent supported languages ->
          :class:`LanguageCode` returned
        * Alexa locale is not in Agent supported languages, but there's a
          fallback available (e.g. "en-US" can fallback on "en" or "en-GB") ->
          :class:`LanguageCode` returned
        """
        language_code = LOCALE_MAP[locale_str]
        if not language_code:
            raise KeyError(f"Locale {locale_str} is not supported by Intents")

        return match_agent_language(self.agent_cls, language_code)

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

    def entity_language_data(self, entity_cls: Type[EntityMixin], lang: LanguageCode=None):
        return self._entity_language_data(self.agent_cls, entity_cls, lang)

    @staticmethod
    def _entity_language_data(
        agent_cls: Type[Agent],
        entity_cls: Type[EntityMixin],
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
    def entry_value_id(entity_cls: Type[EntityMixin], entry: AlexaEntityEntry):
        """
        Entity entries in Alexa have IDs. This is a centralized function to
        compute them.
        """
        return entity_cls.name + "-" + entry.alexa_value.replace(" ", "") # TODO: refine


def _is_valid_entity_value(val: str):
    # TODO: refine
    return bool(re.match(r'^[a-zA-Z0-9\s]+$', val))
