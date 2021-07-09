"""
Official Request/Response schemas: https://github.com/alexa/alexa-apis-for-python/tree/master/ask-sdk-model/ask_sdk_model
"""
import json

from intents import Agent, Intent
from intents.service_connector import Connector, ServiceEntityMappings
from intents.connectors.alexa.export import render
from intents.connectors.alexa.slot_types import ENTITY_MAPPINGS

class AlexaConnector(Connector):
    """
    This is an implementation of :class:`Connector` that enables Agents to
    work as Alexa projects.

    NOTE: This connector is experimental
    """
    entity_mappings: ServiceEntityMappings = ENTITY_MAPPINGS

    invocation_name: str

    def __init__(
        self,
        agent_cls: type(Agent),
        invocation_name: str,
        default_session: str=None,
        default_language: str="en"
    ):
        super().__init__(agent_cls, default_session=default_session,
                         default_language=default_language)
        self.invocation_name = invocation_name # TODO: model constraints
    
    def export(self, destination: str):
        rendered = render(self)
        for lang, data in rendered.items():
            with open(f"TMP_ALEXA.{lang.value}.json", "w") as f:
                json.dump(data, f, indent=4)

    def upload(self):
        raise NotImplementedError()

    def predict(self, message: str, session: str = None, language: str = None) -> Intent:
        raise NotImplementedError()

    def trigger(self, intent: Intent, session: str=None, language: str=None) -> Intent:
        raise NotImplementedError()
