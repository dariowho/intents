from typing import List
from dataclasses import field

import pytest

from intents import Intent, Sys
from intents.model.intent import IntentParameterMetadata
from intents.service_connector import Prediction
from intents import language

def test_param_scheme_no_params():

    class no_param_intent(Intent):
        """Simple Intent with no parameters"""

    assert no_param_intent.parameter_schema() == {}

def test_param_scheme_with_params():

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

def test_param_scheme_invalid_list_default():
    
    with pytest.raises(ValueError):

        class intent_with_invalid_list_default(Intent):
            """Intent with parameters"""
            optional_list_param: List[Sys.Person] = 42

def test_fulfillment_messages():
    class MockPredictionImplementation(Prediction):
        @property
        def entity_mappings(self):
            return None

    mock_default_messages = [
        language.TextIntentResponse(choices=["If you like I can recommend you an hotel. Or I can send you some holiday pictures"])
    ]
    mock_rich_messages = [
        language.TextIntentResponse(choices=["I also like travels, how can I help you?"]),
        language.QuickRepliesIntentResponse(replies=["Recommend an hotel", "Send holiday photo"])
    ]
    mock_prediction = MockPredictionImplementation(
        intent_name='fake_intent_name',
        confidence=0.5,
        contexts={},
        parameters_dict={},
        fulfillment_messages={
            language.IntentResponseGroup.DEFAULT: mock_default_messages,
            language.IntentResponseGroup.RICH: mock_rich_messages
        },
        fulfillment_text="Fake fulfillment text"
    )

    class fake_intent(Intent):
        pass

    predicted = fake_intent.from_prediction(mock_prediction)

    assert predicted.fulfillment_messages() == mock_rich_messages
    assert predicted.fulfillment_messages(language.IntentResponseGroup.DEFAULT) == mock_default_messages
    assert predicted.fulfillment_messages(language.IntentResponseGroup.RICH) == mock_rich_messages
