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
from typing import List, Union
from dataclasses import dataclass

import yaml

import dialogflow_agents
from dialogflow_agents.model.intent import _IntentMetaclass
from dialogflow_agents.model.entity import _EntityMetaclass

logger = logging.getLogger(__name__)

def agent_language_folder(agent_cls: type):
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
    
    # TODO: check for escape characters
    def __init__(self, example: str, intent: dialogflow_agents.Intent):
        self._intent = intent
        self.chunks() # Will check parameters
    
    def __new__(cls, example: str, intent: dialogflow_agents.Intent):
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
                raise ValueError(f"Example '{self}' references parameter ${parameter_name}, but intent {self._intent.metadata.name} does not define such parameter.")
 
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

def intent_language_data(agent_cls: type, intent: _IntentMetaclass) -> (List[ExampleUtterance], List[ResponseUtterance]):
    language_folder = agent_language_folder(agent_cls)

    # TODO: support multiple languages
    language_file = os.path.join(language_folder, "intents", f"{intent.metadata.name}__en.yaml")
    if not os.path.isfile(language_file):
        raise ValueError(f"Language file not found for intent '{intent.metadata.name}'. Expected path: {language_file}. Language files are required even if the intent doesn't need language; in this case, use an empty file.")
    
    with open(language_file, 'r') as f:
        language_data = yaml.load(f.read(), Loader=yaml.FullLoader)

    if not language_data:
        return [], []

    examples_data = language_data.get('examples', [])
    responses_data = language_data.get('responses', [])

    examples = [ExampleUtterance(s, intent) for s in examples_data]
    responses = _build_responses(responses_data)

    return examples, responses

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

def entity_language_data(agent_cls: type, entity_cls: _EntityMetaclass) -> List[EntityEntry]:
    language_folder = agent_language_folder(agent_cls)

    # TODO: support other languages
    language_file = os.path.join(language_folder, "entities", f"{entity_cls.name}__en.yaml")
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

    return entries

# from example_agent import ExampleAgent
# from example_agent.intents import smalltalk

# examples, responses = intent_language_data(ExampleAgent, smalltalk.user_name_give)
# for e in examples:
#     print(e.chunks())

# from example_agent import ExampleAgent
# from example_agent.intents.restaurant import PizzaType

# entity_language_data(ExampleAgent, PizzaType)
