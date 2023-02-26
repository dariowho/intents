"""
A Command Line Interface for Agents is available through the **agentctl** script.

.. warning::

    **agentctl** is experimental, expect its interface and implementation to change in the near future

To use the CLI, define first define an ``.env`` file with the Agent configuration parameters. You can find an example at ``/example_agent/test_stories/.env.template``.
"""

import logging

import fire
import dotenv

from intents import fulfillment
from intents.cli.agent_controller import AgentController

logger = logging.getLogger(__name__)

class Agentctl:
    """
    This is the base Agentclt class.
    """

    def export(self, path: str):
        """
        Export the Agent to file

            >>> dotenv -f .env run agentctl export --path my_agent.zip

        Args:
            path: path to the file the Agent will be exported to
        """
        controller = AgentController.from_env()
        print(f"Exporting Agent '{controller.agent_class_import}' to '{path}' using connector: {controller.connector}")
        connector = controller.load_connector()
        connector.export(path)

    def upload(self):
        """
        Upload the Agent its configured service

            >>> dotenv -f .env run agentctl upload
        """
        controller = AgentController.from_env()
        print(f"Uploading Agent '{controller.agent_class_import}' using connector: {controller.connector}")
        connector = controller.load_connector()
        connector.upload()

    def dev_server(self):
        """
        Start a development server to enable fulfillments.

            >>> dotenv -f .env run agentctl upload

        Make sure that your server is reachable from the prediction service (e.g. by using a *ngrok* 
        tunnel if you are developing locally) on the host and port defined by the ``I_WEBHOOK_HOST`` 
        and ``I_WEBHOOK_PORT`` env variables; the remote agent will be configured to use those values 
        in :meth:`Agentctl.upload`.
        """
        controller = AgentController.from_env()
        print(f"Starting Dev server for Agent '{controller.agent_class_import}' using connector: {controller.connector}")
        connector = controller.load_connector()
        fulfillment.run_dev_server(
            connector=connector,
            token=controller.webhook_configuration.token,
            port=controller.dev_server_port
        )

def agentctl():
    dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True), verbose=True)
    logger.warning("Warning! agentctl is a preview feature, its behavior may not be stable or consistent.")
    fire.Fire(Agentctl)
