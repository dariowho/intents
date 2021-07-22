import os
import tempfile

from example_agent import ExampleAgent
from intents.connectors.dialogflow_es import export, connector, entities

class MockDialogflowConnector(connector.DialogflowEsConnector):

    def __init__(self):
        pass

    agent_cls: type = ExampleAgent
    gcp_project_id: str = "fake-project-id"
    rich_platforms: tuple = ("telegram", "slack")
    webhook_configuration = None
    entity_mappings = entities.MAPPINGS
    _need_context_set = connector._build_need_context_set(ExampleAgent)

def test_export_example_agent_no_exceptions():
    with tempfile.TemporaryDirectory() as temp_dir:
        export.export(MockDialogflowConnector(), os.path.join(temp_dir, 'TMP_AGENT.zip'))
