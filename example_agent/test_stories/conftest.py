import dotenv
dotenv.load_dotenv()

import os
import sys
import pytest

from pathlib import Path

from intents.testing import AgentTester
from intents.connectors import DialogflowEsConnector, WebhookConfiguration

from example_agent import ExampleAgent

# You want to add the folder that contains your project's main package. In this
# case, `example_agent/` is located two directories up
sys.path.append(Path(os.path.dirname(__file__)).parent.parent.absolute())

# Configuration is loaded from `.env`. Make sure to create it from the included `template.env`
if "DIALOGFLOW_CREDENTIALS" not in os.environ:
    raise KeyError("Dialogflow credentials are required, but not found in .env. Make sure to deploy your agent, setup a ngrok-like tunnel and create a proper '.env' file (start from 'template.env')")
DF_CREDENTIALS = os.environ["DIALOGFLOW_CREDENTIALS"]
DEV_SERVER_PORT = int(os.getenv("DEV_SERVER_PORT", "8000"))
DEV_SERVER_TOKEN = os.getenv("DEV_SERVER_TOKEN")

# This is a fixture that pytest will pass to each test as a parameter. The
# AgentTester() object can create dialog stories and run assertions on them
@pytest.fixture(scope="session")
def agent_tester() -> AgentTester:
    return get_agent_tester()

@pytest.fixture(scope="function")
def story(agent_tester):
    return agent_tester.story()

def get_agent_tester():
    # Webhook configuration is only used to validate fulfillment requests
    webhook = WebhookConfiguration('https://fake-address.com/', {"X-Intents-Token": DEV_SERVER_TOKEN})
    df = DialogflowEsConnector(
        DF_CREDENTIALS,
        ExampleAgent,
        webhook_configuration=webhook
    )
    return AgentTester(connector=df, dev_server_port=DEV_SERVER_PORT, dev_server_token=DEV_SERVER_TOKEN)
    
if __name__ == "__main__":
    # python ./conftest.py will launch dev server manually, in case debugging is
    # needed
    get_agent_tester()._dev_server_thread.join()
