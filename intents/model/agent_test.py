from typing import List
from dataclasses import dataclass
from unittest.mock import patch, call

import pytest

from intents import Agent, Sys, Intent, Entity
from intents import language
from example_agent import smalltalk

real_LanguageCode = language.LanguageCode

def _get_toy_agent():

    class ToyAgent(Agent):
        languages = ['en']

    return ToyAgent

@patch('intents.language.intent_language_data')
def test_register_intent_valid_language_data(mock_language):
    mock_language.LanguageCode = real_LanguageCode

    MyAgent = _get_toy_agent()
    MyAgent._register_intent(smalltalk.Hello)

    assert MyAgent.intents == [smalltalk.Hello]
    assert MyAgent._intents_by_name == {'smalltalk.Hello': smalltalk.Hello}

    MyAgent = _get_toy_agent()
    MyAgent.register(smalltalk.Hello)

    assert MyAgent.intents == [smalltalk.Hello]
    assert MyAgent._intents_by_name == {'smalltalk.Hello': smalltalk.Hello}

@patch('intents.language.intent_language_data')
def test_register_intent_invalid_language_data(mock_language):
    mock_language.LanguageCode = real_LanguageCode

    mock_language.side_effect = ValueError("Mock language data not found exception")

    MyAgent = _get_toy_agent()
    
    with pytest.raises(ValueError):
        MyAgent._register_intent(smalltalk.Hello)

@patch('intents.language.intent_language_data')
def test_register_intent_non_unique_name(mock_language):
    @dataclass
    class AnIntent(Intent):
        pass

    @dataclass
    class an_intent(Intent):
        pass

    @dataclass
    class Anintent(Intent):
        pass

    @dataclass
    class AnIntentWithCustomName(Intent):
        name = f"agent_test.An.Intent"

    class MyAgent(Agent):
        pass

    MyAgent.register(AnIntent)

    with pytest.raises(ValueError):
        MyAgent.register(an_intent)

    with pytest.raises(ValueError):
        MyAgent.register(Anintent)

    with pytest.raises(ValueError):
        MyAgent.register(AnIntentWithCustomName)

@patch('intents.language.intent_language_data')
def test_register_intent_non_unique_parameter(mock_language):
    @dataclass
    class an_intent(Intent):
        foo: Sys.Person

    @dataclass
    class a_consistent_intent(Intent):
        foo: Sys.Person
        bar: Sys.Integer

    @dataclass
    class an_inconsistent_intent(Intent):
        foo: Sys.Integer
        bar: Sys.Integer

    @dataclass
    class another_inconsistent_intent(Intent):
        foo: List[Sys.Person]

    class MyAgent(Agent):
        pass

    MyAgent.register(an_intent)
    MyAgent.register(a_consistent_intent)
    
    with pytest.raises(ValueError):
        MyAgent.register(an_inconsistent_intent)

    with pytest.raises(ValueError):
        MyAgent.register(another_inconsistent_intent)

@patch('intents.language.intent_language_data')
def test_register_intent_invalid_param_schema_list_default(mock_language):
    MyAgent = _get_toy_agent()
    
    with pytest.raises(ValueError):
        @dataclass
        class intent_with_invalid_list_default(Intent):
            """Intent with invalid parameter default"""
            optional_list_param: List[Sys.Person] = 42
        
        MyAgent.register(intent_with_invalid_list_default)

@patch('intents.model.agent.language')
def test_register_intent_registers_entities(mock_language):
    mock_language.LanguageCode = real_LanguageCode

    MyAgent = _get_toy_agent()

    class MyEntity(Entity):
        pass

    @dataclass
    class MyIntent(Intent):
        name = "my_intent"

        a_param: Sys.Person
        another_param: MyEntity

    MyAgent._register_intent(MyIntent)

    assert MyAgent.intents == [MyIntent]
    assert MyAgent._intents_by_name == {'my_intent': MyIntent}
    assert MyAgent._entities_by_name == {'MyEntity': MyEntity}

    @dataclass
    class MyOtherIntent(Intent):
        name = "my_other_intent"

        a_param: Sys.Person
        another_param: MyEntity

    MyAgent._register_intent(MyOtherIntent)
    assert MyAgent.intents == [MyIntent, MyOtherIntent]
    assert MyAgent._intents_by_name == {'my_intent': MyIntent, 'my_other_intent': MyOtherIntent}
    assert MyAgent._entities_by_name == {'MyEntity': MyEntity} # MyEntity is not registered twice
    
    def _make_duplicate_entity():
        class MyEntity(Entity):
            """Same name, different class"""
            pass
        return MyEntity

    @dataclass
    class MyInvalidIntent(Intent):
        name = "my_invalid_intent"

        a_param: Sys.Person
        another_param: _make_duplicate_entity()

    with pytest.raises(ValueError):
        MyAgent._register_intent(MyInvalidIntent) # Different entities with same name raise Error

@patch('intents.model.agent.language')
def test_register_module(mock_language):
    mock_language.LanguageCode = real_LanguageCode
    MyAgent = _get_toy_agent()
    with patch.object(MyAgent, '_register_intent') as mock_register_intent:
        MyAgent.register(smalltalk)
        mock_register_intent.asssert_has_calls([
            call(MyAgent, smalltalk.Hello),
            call(MyAgent, smalltalk.UserNameGive),
            call(MyAgent, smalltalk.AgentNameGive),
            call(MyAgent, smalltalk.UserLikesMusic),
            call(MyAgent, smalltalk.GreetFriends),
        ])
