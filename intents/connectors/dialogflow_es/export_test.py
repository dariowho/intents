import os
import tempfile
from unittest.mock import patch
from dataclasses import dataclass

from example_agent import ExampleAgent
from intents import Agent, Intent, follow
from intents.connectors.dialogflow_es import export, connector, entities, names
from intents.connectors.dialogflow_es import agent_format as df

#
# Testing intents
#

@dataclass
class FollowedIntent(Intent):
    pass

@dataclass
class FollowedIntentSubclass(FollowedIntent):
    pass

@dataclass
class FollowingIntent(Intent):
    parent_followed_intent: FollowedIntent = follow()

@dataclass
class FollowingIntentSubclass(FollowingIntent):
    pass

@dataclass
class FollowingSubclassIntent(Intent):
    parent_followed_intent_subclass: FollowedIntentSubclass = follow()

class MockAgent(Agent):
    pass

with patch('intents.language.intent_language_data'):
    MockAgent.register(FollowedIntent)
    MockAgent.register(FollowedIntentSubclass)
    MockAgent.register(FollowingIntent)
    MockAgent.register(FollowingIntentSubclass)
    MockAgent.register(FollowingSubclassIntent)

#
# Mock Connector
#

class MockDialogflowConnector(connector.DialogflowEsConnector):

    agent_cls: type = None
    _need_context_set = None


    def __init__(self, agent_cls):
        self.agent_cls = agent_cls
        self._need_context_set = connector._build_need_context_set(agent_cls)

    gcp_project_id: str = "fake-project-id"
    rich_platforms: tuple = ("telegram", "slack")
    webhook_configuration = None
    entity_mappings = entities.MAPPINGS

#
# Tests
#

def test_export_example_agent_no_exceptions():
    with tempfile.TemporaryDirectory() as temp_dir:
        export.export(MockDialogflowConnector(ExampleAgent), os.path.join(temp_dir, 'TMP_AGENT.zip'))

def test_get_input_contexts():
    mock_connector = MockDialogflowConnector(MockAgent)
    
    result = export.get_input_contexts(mock_connector, FollowedIntent)
    assert result == []

    result = export.get_input_contexts(mock_connector, FollowedIntentSubclass)
    assert result == []

    result = export.get_input_contexts(mock_connector, FollowingIntent)
    assert result == [names.context_name(FollowedIntent)]

    result = export.get_input_contexts(mock_connector, FollowingIntentSubclass)
    assert result == [names.context_name(FollowedIntent)]

    result = export.get_input_contexts(mock_connector, FollowingSubclassIntent)
    assert result == [names.context_name(FollowedIntentSubclass)]

def test_get_output_contexts():
    mock_connector = MockDialogflowConnector(MockAgent)
    _c = lambda x: names.context_name(x)

    result = export.get_output_contexts(mock_connector, FollowedIntent)
    assert result == [
        df.AffectedContext(name=_c(FollowedIntent), lifespan=5)
    ]

    result = export.get_output_contexts(mock_connector, FollowedIntentSubclass)
    assert result == [
        df.AffectedContext(name=_c(FollowedIntentSubclass), lifespan=5),
        df.AffectedContext(name=_c(FollowedIntent), lifespan=5),
    ]

    result = export.get_output_contexts(mock_connector, FollowingIntent)
    assert result == []

    result = export.get_output_contexts(mock_connector, FollowingIntentSubclass)
    assert result == []

    result = export.get_output_contexts(mock_connector, FollowingSubclassIntent)
    assert result == []

# TODO:
#   - own output context
#   - output context when re-defining lifespan of followed intent
#   - contexts do not appear twice
#   - superclasses are included in new_lifespan case
