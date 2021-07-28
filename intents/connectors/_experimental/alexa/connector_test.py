import tempfile

from example_agent.agent import ExampleAgent
from intents.connectors._experimental.alexa import AlexaConnector

def test_export_example_agent_no_exceptions():
    alexa = AlexaConnector(ExampleAgent, "any invocation")
    with tempfile.TemporaryDirectory() as temp_dir:
        alexa.export(temp_dir)
