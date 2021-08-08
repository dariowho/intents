import os
import tempfile
from unittest.mock import MagicMock

import pytest

from example_agent import ExampleAgent
from intents.language import LanguageCode, IntentResponseGroup, TextIntentResponse
from intents.helpers import coffee_agent as ca 
from intents.connectors._experimental.snips.connector import SnipsConnector
from intents.connectors._experimental.snips.prediction import SnipsPrediction

def test_export_no_errors():
    c = SnipsConnector(ExampleAgent)
    with tempfile.TemporaryDirectory() as d:
        c.export(d)
        assert os.path.isfile(os.path.join(d, "agent.en.json"))

def test_predict_default_language():
    class MockSnipsEngine:
        def parse(self, message):
            return {
                'input': 'I want an espresso',
                'intent': {'intentName': 'AskEspresso', 'probability': 0.677},
                'slots': []
            }
    c = SnipsConnector(ca.CoffeeAgent)
    c.nlu_engines = {
        LanguageCode.ENGLISH: MockSnipsEngine(),
        LanguageCode.ITALIAN: MockSnipsEngine()
    }
    result = c.predict("Fake text, response is mocked anyway...")
    expected_messages = {
        IntentResponseGroup.DEFAULT: [
            TextIntentResponse(choices=["medium roast espresso, good choice!", "Alright, medium roasted espresso for you"])
        ]
    }
    assert result.intent == ca.AskEspresso()
    assert result.confidence == 0.677
    assert result.fulfillment_messages == expected_messages
    with pytest.warns(DeprecationWarning):
        assert result.fulfillment_message_dict == expected_messages
