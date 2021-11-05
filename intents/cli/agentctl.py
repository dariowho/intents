import logging

import fire
import dotenv

from intents import connectors
from intents import fulfillment
from intents.cli.agent_controller import AgentController

logger = logging.getLogger(__name__)

class Agentctl:

    def upload(self):
        controller = AgentController.from_env()
        print(f"Uploading Agent '{controller.agent_class_import}' using connector: {controller.connector}")
        connector = controller.load_connector()
        connector.upload()

    def dev_server(self):
        controller = AgentController.from_env()
        print(f"Starting Dev server for Agent '{controller.agent_class_import}' using connector: {controller.connector}")
        connector = controller.load_connector()
        fulfillment.run_dev_server(connector=connector, token=controller.webhook_configuration.token)

def agentctl():
    dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True), verbose=True)
    logger.warning("Warning! agentctl is a preview feature, its behavior may not be stable or consistent.")
    fire.Fire(Agentctl)
