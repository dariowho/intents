"""
Here we convert Intent object names into names that will be used in Alexa
"""
from typing import Dict

from intents.types import AgentType, IntentType, EntityType
from intents.connectors._experimental.alexa import slot_types

class AlexaNamesComponent:
    agent_cls: AgentType

    _alexa_to_intent_name: Dict[str, str]
    _alexa_entry_id_to_canonical: Dict[str, str]

    def __init__(self, agent_cls: AgentType):
        self.agent_cls = agent_cls
        self._alexa_to_intent_name = {}

        self._build_indices(agent_cls)

    def _build_indices(self, agent_cls: AgentType):
        for intent_cls in agent_cls.intents:
            alexa_name = self.intent_to_alexa(intent_cls)
            self._alexa_to_intent_name[alexa_name] = intent_cls.name

    def alexa_to_intent_name(self, alexa_name: str) -> str:
        """
        Convert an Intent name, as it is referenced in the Alexa agent
        """
        return self._alexa_to_intent_name[alexa_name]

    @staticmethod
    def intent_to_alexa(intent_cls: IntentType) -> str:
        """
        Generate the Intent name that will be used in the Alexa export
        """
        return intent_cls.name.replace(".", "_")

    @staticmethod
    def entity_service_name(entity_cls: EntityType):
        # TODO: may be necessary to sanitize custom entity names
        return slot_types.ENTITY_MAPPINGS.service_name(entity_cls)
