"""
This is a connector that can export an :class:`Agent` to the **Alexa** format.

.. warning::

    Alexa connector is **experimental**, it is published mainly to study the case and gather
    feedback: expect relevant rough edges. Also,

    * `predict` and `trigger` are not implemented (you don't call Alexa, Alexa calls you)
    * Entities :class:`Sys.Email` and :class:`Sys.Url` are not available in Alexa (regex entites aren't supported either, which makes it difficult to work around this one)
    * Responses are managed with fulfillment, which is not implemented
    * Intent relations are not considered

Official Request/Response schemas:
https://github.com/alexa/alexa-apis-for-python/tree/master/ask-sdk-model/ask_sdk_model
"""
import os
import json
import shutil
import logging

from intents import Agent, Intent, Entity
from intents.model.fulfillment import FulfillmentRequest
from intents.language import entity_language
from intents.service_connector import Connector, ServiceEntityMappings
from intents.connectors._experimental.alexa.export import render
from intents.connectors._experimental.alexa.slot_types import ENTITY_MAPPINGS

logger = logging.getLogger(__name__)

class AlexaConnector(Connector):
    """
    This is an implementation of :class:`Connector` that enables Agents to
    work as Alexa projects.

    .. warning::

        This connector is **experimental**. Features may not be complete and
        behavior may change in next releases.

    At the moment, all you can do is to :meth:`export` an Agent in the Alexa format
    (note that contexts are not considered, and responses are not included;
    webhook fulfillment needs to be implemented for both).
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
        """
        Export Agent in the given folder:

        .. code-block:: python

            from example_agent.agent import ExampleAgent
            from intents.connectors._experimental.alexa import AlexaConnector

            alexa = AlexaConnector(ExampleAgent, "any invocation")
            alexa.export("./TMP_ALEXA")

        The export will generate one JSON file per language, they can be imported
        from the Alexa console. Destination will be overwritten if already existing.
        """
        rendered = render(self)

        if os.path.isdir(destination):
            logger.warning("Removing existing export folder: %s", destination)
            shutil.rmtree(destination)
        os.makedirs(destination)

        for lang, data in rendered.items():
            with open(os.path.join(destination, f"agent.{lang.value}.json"), "w") as f:
                json.dump(data, f, indent=4)

    def upload(self):
        """
        *Not implemented*
        """
        raise NotImplementedError()

    def predict(self, message: str, session: str = None, language: str = None) -> Intent:
        """
        *Not implemented*
        """
        raise NotImplementedError()

    def trigger(self, intent: Intent, session: str=None, language: str=None) -> Intent:
        """
        *Not implemented*
        """
        raise NotImplementedError()

    def fulfill(self, fulfillment_request: FulfillmentRequest) -> dict:
        """
        *Not implemented*
        """
        raise NotImplementedError()

    def entity_value_id(self, entity_cls: type(Entity), entity_value: entity_language.EntityEntry):
        """
        Entity entries in Alexa have IDs. This is a centralized function to
        compute them.
        """
        return entity_cls.name + entity_value.value
