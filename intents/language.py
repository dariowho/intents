"""
Utilities to manage the Agent's language resources. An Agent is defined as a
Python package. The package is expected to have a `language` folder at its top
level, containing language resources for intents and entities, in the for of
YAML files.

TODO: expand
"""
import os
import re
import sys
import logging
from enum import Enum
from typing import List, Dict, Union
from dataclasses import dataclass

import yaml

import intents
from intents.model.intent import _IntentMetaclass
from intents.model.entity import _EntityMetaclass

logger = logging.getLogger(__name__)

class LanguageCode(Enum):

    ENGLISH = 'en'
    ENGLISH_US = 'en_US'
    ENGLISH_UK = 'en_UK'
    ITALIAN = 'it'
    SPANISH = 'es'
    SPANISH_SPAIN = 'es_ES'
    SPANISH_LATIN_AMERICA = 'es_LA'
    GERMAN = 'de'
    FRENCH = 'fr'
    DUTCH = 'nl'
    CHINESE = 'zh'
    CHINESE_PRC = 'zh_CN'
    CHINESE_HONG_KONG = 'zh_HK'

LANGUAGE_CODES = [x.value for x in LanguageCode]

#
# Agent
#

def agent_language_folder(agent_cls: "agent._AgentMetaclass") -> str:
    main_agent_package_name = agent_cls.__module__.split('.')[0]
    main_agent_package = sys.modules[main_agent_package_name]
    if '__path__' not in main_agent_package.__dict__:
        # TODO: try workdir or something...
        logger.warning("Agent %s doesn't seem to be defined within a package. Language data will not be loaded.", agent_cls)
        return [], []

    agent_folder = main_agent_package.__path__[0]
    language_folder = os.path.join(agent_folder, 'language')
    if not os.path.isdir(language_folder):
        raise ValueError(f"No language folder found for agent {agent_cls} (expected: {language_folder})")

    return language_folder

def agent_supported_languages(agent_cls: "agent._AgentMetaclass") -> List[LanguageCode]:
    result = []
    
    language_folder = agent_language_folder(agent_cls)
    for f in os.scandir(language_folder):
        if f.is_dir() and not f.name.startswith('.')  and not f.name.startswith('_'):
            if f.name in LANGUAGE_CODES:
                result.append(LanguageCode(f.name))
            else:
                logger.warning("Unrecognized language code: '%s' (must be one of %s). Skipping language data.", f.name, LANGUAGE_CODES)
        
    return result

#
# Intent Language Data
#

class UtteranceChunk:
    """
    An Example Utterance can be seen as a sequence of Chunks, where each Chunk
    is either a mapped Entity, or a plain text string.
    """

@dataclass
class TextUtteranceChunk(UtteranceChunk):
    """
    An Utterance Chunk that is a static, plain text string.
    """
    text: str

@dataclass
class EntityUtteranceChunk(UtteranceChunk):
    """
    An Utterance Chunk that is a matched entity
    """
    entity_cls: _EntityMetaclass
    parameter_name: str
    parameter_value: str

# TODO: check that parameter_value is one of the entries in custom entities
RE_EXAMPLE_PARAMETERS = re.compile(r"\$(?P<parameter_name>[\w]+)\{(?P<parameter_value>[^\}]+)\}")

class ExampleUtterance(str):
    """
    One of the example Utterances of a given Intent.
    """
    
    # TODO: check for escape characters - intent is possibly intent_cls
    def __init__(self, example: str, intent: intents.Intent):
        self._intent = intent
        self.chunks() # Will check parameters
    
    def __new__(cls, example: str, intent: intents.Intent):
        return super().__new__(cls, example)

    def chunks(self):
        """
        Return the Utterance as a sequence of :class:`UtteranceChunk`. Each
        chunk is either a plain text string, or a mapped Entity.

        >>> utterance = ExampleUtterance("My name is $user_name{Guido}!", intents.user_gives_name)
        >>> utterance.chunks()
        [
            TextUtteranceChunk(text="My name is "),
            EntityUtteranceChunk(entity_cls=Sys.Person, parameter_name="user_name", parameter_value="Guido"),
            TextUtteranceChunk(text="!")
        ]

        TODO: handle escaping
        """
        parameter_schema = self._intent.parameter_schema()
        result = []
        last_end = 0
        for m in RE_EXAMPLE_PARAMETERS.finditer(self):
            m_start, m_end = m.span()
            m_groups = m.groupdict()
            if m_start > 0:
                result.append(TextUtteranceChunk(text=self[last_end:m_start]))
            
            if (parameter_name := m_groups['parameter_name']) not in parameter_schema:
                raise ValueError(f"Example '{self}' references parameter ${parameter_name}, but intent {self._intent.name} does not define such parameter.")
 
            entity_cls = parameter_schema[parameter_name].entity_cls
            result.append(EntityUtteranceChunk(
                entity_cls=entity_cls,
                parameter_name=m_groups['parameter_name'],
                parameter_value=m_groups['parameter_value']
            ))

            last_end = m_end

        last_chunk = TextUtteranceChunk(text=self[last_end:])
        if last_chunk.text:
            result.append(last_chunk)

        return result

class ResponseUtterance:
    """
    One of the Response Utterances of a given Intent.
    """

class TextResponseUtterance(ResponseUtterance):
    """
    A plain text response. The actual response is picked randomly from a pool of
    choices.
    """

    choices: List[str]

    def __init__(self, choices: Union[str, List[str]]):
        if not isinstance(choices, list):
            assert isinstance(choices, str)
            choices = [choices]

        self.choices = choices

    def __hash__(self):
        return "".join(self.choices).__hash__()

    def __eq__(self, other):
        if not isinstance(other, TextResponseUtterance):
            return False
        return self.choices == other.choices
    
    def __str__(self):
        return f"<TextResponseUtterance: {self.choices}>"

    def __repr__(self):
        return str(self)

@dataclass
class IntentLanguageData:
    """
    Language data for an Intent consists of three resources:

    * Example Utterances
    * Slot Filling Prompts
    * Responses

    Example Utterances are the messages that Agent will be trained on to
    recognize the Intent.

    Responses, intuitively, are the Agent's response messages that will be sent
    to User once the Intent is recognized.

    Slot Filling Promps are used to solve parameters that couldn't be tagged in
    the original message. For instance a `order_pizza` intent may have a
    `pizza_type` parameter. When User asks "I'd like a pizza" we want to fill
    the slot by asking "What type of pizza?". `slot_filling_prompts` will map
    parameters to their prompts: `{"pizza_type": ["What type of pizza?"]}`
    """
    example_utterances: List[ExampleUtterance]
    slot_filling_prompts: Dict[str, List[str]]
    responses: List[ResponseUtterance]

def intent_language_data(agent_cls: "agent._AgentMetaclass", intent_cls: _IntentMetaclass, language_code: LanguageCode=None) -> Dict[LanguageCode, IntentLanguageData]:
    language_folder = agent_language_folder(agent_cls)

    if not language_code:
        result = {}
        for language_code in agent_cls.languages:
            language_data = intent_language_data(agent_cls, intent_cls, language_code)
            result[language_code] = language_data[language_code]
        return result

    if isinstance(language_code, str):
        language_code = LanguageCode(language_code)

    language_file = os.path.join(language_folder, language_code.value, f"{intent_cls.name}.yaml")
    if not os.path.isfile(language_file):
        raise ValueError(f"Language file not found for intent '{intent_cls.name}'. Expected path: {language_file}. Language files are required even if the intent doesn't need language; in this case, use an empty file.")
    
    with open(language_file, 'r') as f:
        language_data = yaml.load(f.read(), Loader=yaml.FullLoader)

    if not language_data:
        return IntentLanguageData([], {}, [])

    examples_data = language_data.get('examples', [])
    responses_data = language_data.get('responses', [])

    examples = [ExampleUtterance(s, intent_cls) for s in examples_data]
    responses = _build_responses(responses_data)

    language_data = IntentLanguageData(
        example_utterances=examples,
        slot_filling_prompts=language_data.get('slot_filling_prompts', {}),
        responses=responses
    )

    return {language_code: language_data}

def _build_responses(responses_data: dict):
    result = []

    platform: str
    responses: List[dict]
    for platform, responses in responses_data.items():
        if platform != 'default':
            raise NotImplementedError(f"Unsupported platform '{platform}'. Currently, only 'default' is supported")
        for r in responses:
            assert len(r) == 1
            for r_type, r_data in r.items():
                if r_type != 'text':
                    raise NotImplementedError(f"Unsupported response type '{r_type}'. Currently, only 'text' is supported")
                result.append(TextResponseUtterance(r_data))

    return result

#
# Entities
#

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

# from example_agent import ExampleAgent
# from example_agent import smalltalk

# examples, responses = intent_language_data(ExampleAgent, smalltalk.user_name_give)
# for e in examples:
#     print(e.chunks())

# from example_agent import ExampleAgent
# from example_agent.restaurant import PizzaType

# entity_language_data(ExampleAgent, PizzaType)
