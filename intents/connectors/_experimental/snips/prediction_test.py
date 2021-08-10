from unittest.mock import MagicMock
from dataclasses import dataclass
from typing import List

import pytest

from intents import Agent, Intent, Sys
from intents.helpers import coffee_agent as ca
from intents.language import LanguageCode, IntentResponseGroup
from intents.connectors._experimental.snips import prediction_format as pf
from intents.connectors._experimental.snips import prediction, entities

def _get_prediction_component():
    return prediction.SnipsPredictionComponent(ca.CoffeeAgent, entities.ENTITY_MAPPINGS)

def test_prediction_from_parse_renders_language():
    prediction_component = _get_prediction_component()
    prediction_component.intent_from_parse_result = MagicMock(return_value=ca.AskEspresso(roast="dark"))
    parse_result = pf.from_dict({
        'input': 'fake message',
        'intent': {'intentName': 'fake intent', 'probability': 0.677},
        'slots': []
    })
    result = prediction_component.prediction_from_parse_result(parse_result, LanguageCode.ENGLISH)
    assert result.fulfillment_text in ["dark roast espresso, good choice!", "Alright, dark roasted espresso for you"]
    
    messages = result.fulfillment_messages.for_group(IntentResponseGroup.DEFAULT)
    assert messages
    assert messages[0].choices == ["dark roast espresso, good choice!", "Alright, dark roasted espresso for you"]
    
    with pytest.warns(DeprecationWarning):
        messages = result.fulfillment_messages(IntentResponseGroup.DEFAULT)
        assert messages
        assert messages[0].choices == ["dark roast espresso, good choice!", "Alright, dark roasted espresso for you"]

def test_intent_from_parse__default_parameter():
    parse_result = {
        'input': 'I want an espresso',
        'intent': {'intentName': 'AskEspresso', 'probability': 0.677},
        'slots': []
    }
    prediction_component = _get_prediction_component()
    result = prediction_component.intent_from_parse_result(pf.from_dict(parse_result))
    assert result == ca.AskEspresso()


def test_intent_from_parse__single_parameter_single_slot():
    parse_result = {
        'input': 'I want a dark roast espresso',
        'intent': {'intentName': 'AskEspresso', 'probability': 0.56},
        'slots': [
            {
                'range': {'start': 9, 'end': 13},
                'rawValue': 'dark',
                'value': {'kind': 'Custom', 'value': 'dark'},
                'entity': 'CoffeeRoast',
                'slotName': 'roast'
            }
        ]
    }
    prediction_component = _get_prediction_component()
    result = prediction_component.intent_from_parse_result(pf.from_dict(parse_result))
    assert result == ca.AskEspresso(roast="dark")

def test_intent_from_parse__single_parameter_list_slot():
    parse_result = {
        'input': 'I want a dark roast espresso',
        'intent': {'intentName': 'AskEspresso', 'probability': 0.56},
        'slots': [
            {
                'range': {'start': 9, 'end': 13},
                'rawValue': 'dark',
                'value': {'kind': 'Custom', 'value': 'dark'},
                'entity': 'CoffeeRoast',
                'slotName': 'roast'
            },
            {
                'range': {'start': 14, 'end': 19},
                'rawValue': 'light',
                'value': {'kind': 'Custom', 'value': 'light'},
                'entity': 'CoffeeRoast',
                'slotName': 'roast'
            }
        ]
    }
    prediction_component = _get_prediction_component()

    with pytest.warns(None):
        result = prediction_component.intent_from_parse_result(pf.from_dict(parse_result))
    assert result == ca.AskEspresso(roast="dark")

def test_intent_from_parse__list_parameter_list_slot():
    parse_result = {
        'input': 'My colors are green and red',
        'intent': {
            'intentName': 'UserSaysManyColors',
            'probability': 0.66
        },
        'slots': [
            {
                'range': {'start': 14, 'end': 19},
                'rawValue': 'green',
                'value': {'kind': 'Custom', 'value': 'Green'},
                'entity': 'I_IntentsColor',
                'slotName': 'user_color_list'
            }, {
                'range': {'start': 24, 'end': 27},
                'rawValue': 'red',
                'value': {'kind': 'Custom', 'value': 'Red'},
                'entity': 'I_IntentsColor',
                'slotName': 'user_color_list'
            }
        ]
    }

    @dataclass
    class UserSaysManyColors(Intent):
        name = "UserSaysManyColors"
        user_color_list: List[Sys.Color]
    UserSaysManyColors.__intent_language_data__ = ca.mock_language_data(
        UserSaysManyColors,
        ["My colors are $user_color_list{red}, $user_color_list{green} and $user_color_list{blue}", "I give you some colors $user_color_list{yellow}, $user_color_list{orange} and also $user_color_list{purple}"],
        ["$user_color it is"],
        LanguageCode.ENGLISH
    )

    class MyAgent(Agent):
        languages = ['en']
    MyAgent.register(UserSaysManyColors)

    prediction_component = prediction.SnipsPredictionComponent(MyAgent, entities.ENTITY_MAPPINGS)
    
    parse_result = pf.from_dict(parse_result)
    print("NAME", parse_result.intent.intentName)
    result = prediction_component.intent_from_parse_result(parse_result)
    assert result == UserSaysManyColors(user_color_list=['Green', 'Red'])

def test_intent_from_parse__list_parameter_single_slot():
    parse_result = {
        'input': 'My colors are green and red',
        'intent': {
            'intentName': 'UserSaysManyColors',
            'probability': 0.66
        },
        'slots': [
            {
                'range': {'start': 14, 'end': 19},
                'rawValue': 'green',
                'value': {'kind': 'Custom', 'value': 'Green'},
                'entity': 'I_IntentsColor',
                'slotName': 'user_color_list'
            }
        ]
    }

    @dataclass
    class UserSaysManyColors(Intent):
        name = "UserSaysManyColors"
        user_color_list: List[Sys.Color]
    UserSaysManyColors.__intent_language_data__ = ca.mock_language_data(
        UserSaysManyColors,
        ["My colors are $user_color_list{red}, $user_color_list{green} and $user_color_list{blue}", "I give you some colors $user_color_list{yellow}, $user_color_list{orange} and also $user_color_list{purple}"],
        ["$user_color it is"],
        LanguageCode.ENGLISH
    )

    class MyAgent(Agent):
        languages = ['en']
    MyAgent.register(UserSaysManyColors)

    prediction_component = prediction.SnipsPredictionComponent(MyAgent, entities.ENTITY_MAPPINGS)
    
    parse_result = pf.from_dict(parse_result)
    print("NAME", parse_result.intent.intentName)
    result = prediction_component.intent_from_parse_result(parse_result)
    assert result == UserSaysManyColors(user_color_list=['Green'])

#
# Fulfillment
#

def test_fulfillment_recursion_is_blocked():
    # TODO: set timeout on this test

    @dataclass
    class RecursiveFulfillmentIntent(Intent):
        def fulfill(self, context):
            return RecursiveFulfillmentIntent()

    RecursiveFulfillmentIntent.__intent_language_data__ = ca.mock_language_data(
        RecursiveFulfillmentIntent, [], ["fake response"], LanguageCode.ENGLISH
    )

    class MyAgent(Agent):
        languages = ['en']
    MyAgent.register(RecursiveFulfillmentIntent)

    prediction_component = prediction.SnipsPredictionComponent(MyAgent, entities.ENTITY_MAPPINGS)
    pred = prediction_component.prediction_from_intent(RecursiveFulfillmentIntent(), LanguageCode.ENGLISH)
    with pytest.raises(RecursionError):
        prediction_component.fulfill_local(pred, LanguageCode.ENGLISH)
