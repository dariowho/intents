import os
import sys
import logging
from typing import List

from intents.language.language_codes import LanguageCode, LANGUAGE_CODES

logger = logging.getLogger(__name__)

def agent_language_folder(agent_cls: "agent.AgentType") -> str:
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

def agent_supported_languages(agent_cls: "agent.AgentType") -> List[LanguageCode]:
    if agent_cls.languages:
        return agent_cls.languages
        
    result = []
    
    language_folder = agent_language_folder(agent_cls)
    for f in os.scandir(language_folder):
        if f.is_dir() and not f.name.startswith('.')  and not f.name.startswith('_'):
            if f.name in LANGUAGE_CODES:
                result.append(LanguageCode(f.name))
            else:
                logger.warning("Unrecognized language code: '%s' (must be one of %s). Skipping language data.", f.name, LANGUAGE_CODES)
        
    return result
