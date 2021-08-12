"""
Language resources are defined separately from :class:`Intent` and
:class:`Entity` classes. They are stored as plain YAML files in a `language/`
folder, aside Agent Python modules; this is to be flexible in the relationship
with designers and translators, as well as to allow some degree of automation
when downloading cloud changes back to the local Agent definition (this feature
is currently not implemented).

Your `language/` folder will contain one subfloder per language (i.e.
`language/en/`, `language/it/`, ...); each of these will contain

* one YAML file per Intent (e.g. `my_module.my_intent_class.yaml`). Intent
  language resources are specified in :mod:`intents.language.intent_language`
* one YAML file per entity (e.g. `ENTITY_MyEntityClass.yaml`). Entity language
  resources are specified in :mod:`intents.language.entity_language`

.. tip::

    It may be useful to look at The Example Agent code and language resources
    (https://github.com/dariowho/intents/tree/master/example_agent/language)
    to get more insight on the format and naming conventions of language files.
"""
from intents.language_codes import LanguageCode, LANGUAGE_CODES, ensure_language_code
from intents.language.agent_language import agent_language_folder, agent_supported_languages, match_agent_language
from intents.language.intent_language import intent_language_data, IntentResponseGroup, IntentResponseDict, IntentResponse, TextIntentResponse, ImageIntentResponse, QuickRepliesIntentResponse, CardIntentResponse, CustomPayloadIntentResponse, IntentLanguageData, ExampleUtterance, UtteranceChunk, TextUtteranceChunk, EntityUtteranceChunk
from intents.language.entity_language import entity_language_data, EntityEntry
