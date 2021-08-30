"""
This is a connector that can export an :class:`Agent` to the **Alexa** format.

.. warning::

    Alexa connector is **experimental**, it is published mainly to study the case and gather
    feedback: expect relevant rough edges. Also,

    * `predict` and `trigger` are not implemented (you don't call Alexa, Alexa calls you)
    * Entities :class:`Sys.Email` and :class:`Sys.Url` are not available in Alexa (regex entites aren't supported either, which makes it difficult to work around this one)
    * Intent relations are not considered

Official Request/Response schemas:
https://github.com/alexa/alexa-apis-for-python/tree/master/ask-sdk-model/ask_sdk_model
"""
import os
import json
import shutil
import logging

from intents import Agent, Intent
from intents.helpers.data_classes import to_dict
from intents.connectors.interface import Connector, ServiceEntityMappings, FulfillmentRequest
from intents.connectors._experimental.alexa import names, export, language, fulfillment, fulfillment_schemas
from intents.connectors._experimental.alexa.slot_types import ENTITY_MAPPINGS

logger = logging.getLogger(__name__)

class AlexaConnector(Connector):
    """
    This is an implementation of :class:`Connector` that enables Agents to
    work as Alexa projects.

    .. warning::

        This connector is **experimental**. Features may not be complete and
        behavior may change in next releases.

    At the moment, all you can do is to :meth:`export` an Agent in the Alexa
    format, and start the fulfillment development server with
    :func:`~intents.fulfillment.run_dev_server`. You will have to configure your
    Alexa agent from the console to hit your URL instead of its default lambda
    for fulfillment.
    """
    entity_mappings: ServiceEntityMappings = ENTITY_MAPPINGS

    invocation_name: str
    names_component: names.AlexaNamesComponent
    language_component: language.AlexaLanguageComponent
    fulfillment_component: fulfillment.AlexaFulfillmentComponent
    export_component: export.AlexaExportComponent

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
        self.names_component = names.AlexaNamesComponent(agent_cls)
        self.language_component = language.AlexaLanguageComponent(agent_cls)
        self.fulfillment_component = fulfillment.AlexaFulfillmentComponent(
            agent_cls,
            self.names_component,
            self.language_component
        )
        self.export_component = export.AlexaExportComponent(
            agent_cls,
            self.names_component,
            self.language_component,
            invocation_name
        )
    
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
        rendered = self.export_component.render()

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
        logger.warning("Authentication for Alexa fulfillment requests is NOT supported. Do not use AexaConnector in production.")
        body_dict = fulfillment_request.body
        request_body = fulfillment_schemas.from_dict(body_dict)
        response_body = self.fulfillment_component.handle_fulfillment(request_body)
        result = to_dict(response_body)
        return result
