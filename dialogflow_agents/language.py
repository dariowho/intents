"""
Utilities to manage the Agent's language resources. An Agent is defined as a
Python package. The package is expected to have a `language` folder at its top
level, containing language resources for intents and entities, in the for of
YAML files.

TODO: expand
"""
import os
import sys
import logging
from typing import List
from dataclasses import dataclass

import yaml

import dialogflow_agents
from dialogflow_agents.model.intent import IntentMetaclass

logger = logging.getLogger(__name__)

class ExampleUtterance(str):
    pass

class ResponseUtterance(str):
    pass

def intent_language_data(agent_cls: type, intent: IntentMetaclass) -> (List[ExampleUtterance], List[ResponseUtterance]):
    main_agent_package = agent_cls.__module__.split('.')[0]
    agent_folder = sys.modules[main_agent_package].__path__[0]
    language_folder = os.path.join(agent_folder, 'language')
    if not os.path.isdir(language_folder):
        raise ValueError(f"No language folder found for agent {agent_cls} (expected: {language_folder})")
    
    # TODO: support multiple languages
    language_file = os.path.join(language_folder, "intents", f"{intent.metadata.name}__en.yaml")
    if not os.path.isfile(language_file):
        logger.info("Language file not found: %s", language_file)
        return [], []
    
    with open(language_file, 'r') as f:
        language_data = yaml.load(f.read(), Loader=yaml.FullLoader)

    return language_data

# from example_agent import ExampleAgent
# from example_agent.intents import smalltalk

# intent_language_data(ExampleAgent, smalltalk.hello)