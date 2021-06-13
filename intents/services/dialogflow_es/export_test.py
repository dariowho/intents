import os
import tempfile

from example_agent import ExampleAgent
from intents.services.dialogflow_es import export

class MockDialogflowConnector:

    agent_cls: type = ExampleAgent
    gcp_project_id: str = "fake-project-id"
    rich_platforms: tuple = ("telegram", "slack")
    webhook_configuration = None

def test_export_example_agent_no_exceptions():
    with tempfile.TemporaryDirectory() as temp_dir:
        export.export(MockDialogflowConnector(), os.path.join(temp_dir, 'TMP_AGENT.zip'))
