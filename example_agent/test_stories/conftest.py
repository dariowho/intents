import dotenv
dotenv.load_dotenv()

import pytest

from intents.cli.agent_controller import AgentController
from intents.testing import AgentTester

@pytest.fixture(scope="session")
def agent_tester() -> AgentTester:
    controller = AgentController.from_env()
    return controller.load_agent_tester()

@pytest.fixture(scope="function")
def story(agent_tester):
    return agent_tester.story()

if __name__ == "__main__":
    # python ./conftest.py will launch dev server manually, just for debug
    tmp_controller = AgentController.from_env()
    tmp_controller.load_agent_tester()._dev_server_thread.join()
