from typing import List
from dataclasses import field
from unittest.mock import patch

import pytest

from intents import Agent, Intent, Sys
from intents.model.intent import IntentParameterMetadata

def _get_toy_agent():

    class ToyAgent(Agent):
        pass

    return ToyAgent

@patch('intents.language.intent_language_data')
def test_param_scheme_no_params(mock_language):

    ToyAgent = _get_toy_agent()

    @ToyAgent.intent('no_param_intent')
    class no_param_intent(Intent):
        """Simple Intent with no parameters"""

    assert no_param_intent.parameter_schema() == {}

@patch('intents.language.intent_language_data')
def test_param_scheme_with_params(mock_language):

    ToyAgent = _get_toy_agent()

    @ToyAgent.intent('intent_with_params')
    class intent_with_params(Intent):
        """Intent with parameters"""
        required_param: Sys.Person
        required_list_param: List[Sys.Person]
        optional_param: Sys.Person = "John"
        optional_list_param: List[Sys.Person] = field(default_factory=lambda: ["Al", "John"])

    assert intent_with_params.parameter_schema() == {
        "required_param": IntentParameterMetadata(
            name="required_param",
            entity_cls=Sys.Person,
            is_list=False,
            required=True,
            default=None
        ),
        "required_list_param": IntentParameterMetadata(
            name="required_list_param",
            entity_cls=Sys.Person,
            is_list=True,
            required=True,
            default=None
        ),
        "optional_param": IntentParameterMetadata(
            name="optional_param",
            entity_cls=Sys.Person,
            is_list=False,
            required=False,
            default="John"
        ),
        "optional_list_param": IntentParameterMetadata(
            name="optional_list_param",
            entity_cls=Sys.Person,
            is_list=True,
            required=False,
            default=["Al", "John"]
        ),
    }

@patch('intents.language.intent_language_data')
def test_param_scheme_invalid_list_default(mock_language):
    ToyAgent = _get_toy_agent()

    with pytest.raises(ValueError):

        @ToyAgent.intent('intent_with_invalid_list_default')
        class intent_with_invalid_list_default(Intent):
            """Intent with parameters"""
            optional_list_param: List[Sys.Person] = 42
