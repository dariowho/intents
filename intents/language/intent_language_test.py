import os
import tempfile
from typing import List
from unittest.mock import patch
from dataclasses import dataclass

import pytest

from intents import Intent, Sys, Agent, LanguageCode
from intents.helpers.coffee_agent import mock_language_data
from intents.language.intent_language import intent_language_data, IntentLanguageData
from intents.language.intent_language import ExampleUtterance, TextUtteranceChunk, EntityUtteranceChunk
from intents.language.intent_language import IntentResponseDict, IntentResponseGroup, TextIntentResponse, QuickRepliesIntentResponse, ImageIntentResponse, CardIntentResponse, CustomPayloadIntentResponse

@dataclass
class FakeIntent(Intent):
    name = "FakeIntent"

    foo: Sys.Person             # A NLU Parameter
    foo_session: List[float]    # A Session Parameter

#
# Example Utterances
#

def test_utterance_chunks__no_parameters():
    utterance = ExampleUtterance("This is an utterance with no parameters", FakeIntent)
    assert utterance.chunks() == [TextUtteranceChunk("This is an utterance with no parameters")]

    utterance = ExampleUtterance("This is an utterance with no parameters and the $ char: $10", FakeIntent)
    assert utterance.chunks() == [TextUtteranceChunk("This is an utterance with no parameters and the $ char: $10")]
    
def test_utterance_chunks__entity_parameters():
    utterance = ExampleUtterance("$foo{Homer}", FakeIntent)
    assert utterance.chunks() == [
        EntityUtteranceChunk(Sys.Person, "foo", "Homer")
    ]

    utterance = ExampleUtterance("The name is $foo{Homer}", FakeIntent)
    assert utterance.chunks() == [
        TextUtteranceChunk("The name is "),
        EntityUtteranceChunk(Sys.Person, "foo", "Homer")
    ]

    utterance = ExampleUtterance("$foo{Homer} is the name.", FakeIntent)
    assert utterance.chunks() == [
        EntityUtteranceChunk(Sys.Person, "foo", "Homer"),
        TextUtteranceChunk(" is the name."),
    ]

    utterance = ExampleUtterance("The name is $foo{Homer}, I think.", FakeIntent)
    assert utterance.chunks() == [
        TextUtteranceChunk("The name is "),
        EntityUtteranceChunk(Sys.Person, "foo", "Homer"),
        TextUtteranceChunk(", I think."),
    ]

    utterance = ExampleUtterance("The name is \"$foo{Homer}\", I think.", FakeIntent)
    assert utterance.chunks() == [
        TextUtteranceChunk("The name is \""),
        EntityUtteranceChunk(Sys.Person, "foo", "Homer"),
        TextUtteranceChunk("\", I think."),
    ]

def test_utterance_chunks__session_parameters_raise_error():
    with pytest.raises(ValueError):
        ExampleUtterance("The value cannot be \"$foo_session{42}\"...", FakeIntent)

#
# Responses
#

def test_text_intent_response_string():
    text_response_instance = TextIntentResponse(["ciao"])
    text_response_from_yaml = TextIntentResponse.from_yaml("ciao")
    assert text_response_instance == text_response_from_yaml
    assert text_response_from_yaml.choices == ["ciao"]

def test_text_intent_response_list():
    text_response_instance = TextIntentResponse(["pippo", "franco"])
    text_response_from_yaml = TextIntentResponse.from_yaml(["pippo", "franco"])
    assert text_response_instance == text_response_from_yaml
    assert text_response_from_yaml.choices == ["pippo", "franco"]

def test_text_intent_response_equals():
    response_1 = TextIntentResponse(["pippo", "franco"])
    response_2 = TextIntentResponse(["pippo", "franco"])
    response_3 = TextIntentResponse(["franco", "pippo"])
    response_4 = TextIntentResponse(["something", "else"])
    assert response_1 == response_2
    assert response_1 != response_3
    assert response_1 != response_4
    # can't do this with mutable lists
    # assert response_1 in {response_2, response_3, response_4}
    # assert response_1 not in {response_3, response_4}

def test_text_intent_response_random():
    text_response_instance = TextIntentResponse(["pippo", "franco"])
    assert text_response_instance.random() in ["pippo", "franco"]

def test_text_response_render():
    text_response_instance = TextIntentResponse([
        "$foo is when you look at me",
        "I like it when it's $foo",
        "Why does it $foo when I $foobar?",
        "Why does it $foobar when I $foo?",
        "Is it \"$foo\" if it hurts?"
        "$foo"
    ])

    fake_intent = FakeIntent(foo="Trotskyism", foo_session=[])

    expected = TextIntentResponse([
        "Trotskyism is when you look at me",
        "I like it when it's Trotskyism",
        "Why does it Trotskyism when I $foobar?",
        "Why does it $foobar when I Trotskyism?",
        "Is it \"Trotskyism\" if it hurts?"
        "Trotskyism"
    ])

    assert text_response_instance.render(fake_intent) == expected

def test_text_response_render_session_parameter():
    text_response_instance = TextIntentResponse([
        "$foo is a NLU Parameter",
        "$foo_session is a Session Parameter",
    ])

    fake_intent = FakeIntent(foo="Homer", foo_session=[42, 43])

    expected = TextIntentResponse([
        "Homer is a NLU Parameter",
        "[42, 43] is a Session Parameter",
    ])

    assert text_response_instance.render(fake_intent) == expected

def test_quick_replies_response_string():
    quick_replies_instance = QuickRepliesIntentResponse(["ciao"])
    quick_replies_from_yaml = QuickRepliesIntentResponse.from_yaml("ciao")
    assert quick_replies_instance == quick_replies_from_yaml
    assert quick_replies_from_yaml.replies == ["ciao"]

def test_quick_replies_render():
    quick_replies_response_instance = QuickRepliesIntentResponse(["$foo", "pippo", "franco $foo"])
    fake_intent = FakeIntent(foo="bar", foo_session=[])
    expected = QuickRepliesIntentResponse(["bar", "pippo", "franco bar"])

def test_quick_replies_response_list():
    quick_replies_response_instance = QuickRepliesIntentResponse(["pippo", "franco"])
    quick_replies_response_from_yaml = QuickRepliesIntentResponse.from_yaml(["pippo", "franco"])
    assert quick_replies_response_instance == quick_replies_response_from_yaml
    assert quick_replies_response_from_yaml.replies == ["pippo", "franco"]

def test_quick_replies_response_too_long():
    with pytest.raises(ValueError):
        QuickRepliesIntentResponse(["pippo", "franco", "chi chi chi, co co co"])
        
    with pytest.raises(ValueError):
        QuickRepliesIntentResponse.from_yaml(["chi chi chi, co co co", "pippo", "franco"])

    with pytest.raises(ValueError):
        QuickRepliesIntentResponse.from_yaml("chi chi chi, co co co")

def test_image_response_string():
    image_response_instance = ImageIntentResponse(url="https://example.com/image.png")
    image_response_from_yaml = ImageIntentResponse.from_yaml("https://example.com/image.png")
    assert image_response_instance == image_response_from_yaml

def test_image_response_dict():
    image_response_instance = ImageIntentResponse(url="https://example.com/image.png", title="A title")
    image_response_from_yaml = ImageIntentResponse.from_yaml({"url": "https://example.com/image.png", "title": "A title"})
    assert image_response_instance == image_response_from_yaml

def test_custom_payload_response():
    custom_payload_instance = CustomPayloadIntentResponse("any_name", {"foo": "bar"})
    custom_payload_from_yaml = CustomPayloadIntentResponse.from_yaml({
        "any_name": {"foo": "bar"}
    })
    assert custom_payload_instance == custom_payload_from_yaml

def test_card_intent_response():
    card_reponse_instance = CardIntentResponse("Card Title", "a subtitle...")
    card_reponse_from_yaml = CardIntentResponse.from_yaml({
        "title": "Card Title",
        "subtitle":"a subtitle..."
    })
    assert card_reponse_instance == card_reponse_from_yaml

def test_custom_payload_not_dict_data():
    with pytest.raises(ValueError):
        CustomPayloadIntentResponse.from_yaml("foo")

def test_custom_payload_not_dict_value():
    with pytest.raises(ValueError):
        CustomPayloadIntentResponse.from_yaml({"foo": "bar"})

def test_custom_payload_multiple_keys():
    with pytest.raises(ValueError):
        CustomPayloadIntentResponse.from_yaml({
            "any_name": {"foo": "bar"},
            "another_name": {"not": "allowed"}
        })

def test_intent_response_dict_for_group():
    mock_default_messages = ["MOCK DEFAULT 1", "MOCK DEFAULT 2"]
    mock_rich_messages = ["MOCK RICH 1", "MOCK RICH 2"]
    d = IntentResponseDict({
        IntentResponseGroup.DEFAULT: mock_default_messages,
        IntentResponseGroup.RICH: mock_rich_messages
    })
    assert d.for_group() == mock_rich_messages
    assert d.for_group(IntentResponseGroup.DEFAULT) == mock_default_messages
    assert d.for_group(IntentResponseGroup.RICH) == mock_rich_messages

#
# intent_language_data()
#

TOY_LANGUAGE_FILE = """
examples:
  - Hi
  - Hello

responses:
  default:
    - text:
      - Greetings, human :)
      - Hi human!
"""

@dataclass
class MockIntentClass(Intent):
    name: Sys.Person = 'test_intent'

class MockAgentClass(Agent):
    languages = ['en']

def _toy_language_folder(dir_name, intent_name, languages=('en',)):
    for lang in languages:
        lang_dir = os.path.join(dir_name, lang)
        os.makedirs(lang_dir, exist_ok=True)
        with open(os.path.join(lang_dir, intent_name + ".yaml"), 'w') as f:
            print(TOY_LANGUAGE_FILE, file=f)

def test_intent_data_all_languages():
    with tempfile.TemporaryDirectory() as tmp_dir:
        _toy_language_folder(tmp_dir, 'test_intent', ['en'])
        class mock_agent_language_module:
            @staticmethod
            def agent_language_folder(agent_cls):
                return tmp_dir

        with patch('intents.language.intent_language.agent_language', mock_agent_language_module):
            result = intent_language_data(MockAgentClass, MockIntentClass)

    assert LanguageCode.ENGLISH in result
    assert isinstance(result[LanguageCode.ENGLISH], IntentLanguageData)

    assert result[LanguageCode.ENGLISH].example_utterances == [
        ExampleUtterance("Hi", MockIntentClass),
        ExampleUtterance("Hello", MockIntentClass)
    ]
    assert result[LanguageCode.ENGLISH].slot_filling_prompts == {}
    assert result[LanguageCode.ENGLISH].responses == {
        IntentResponseGroup.DEFAULT: [
            TextIntentResponse(["Greetings, human :)", "Hi human!"])
        ]
    }

def test_intent_data_raise_exception_on_session_parameters():
    with tempfile.TemporaryDirectory() as tmp_dir:
        _toy_language_folder(tmp_dir, 'FakeIntent', ['en'])
        class mock_agent_language_module:
            @staticmethod
            def agent_language_folder(agent_cls):
                return tmp_dir

        with patch('intents.language.intent_language.agent_language', mock_agent_language_module):
            with pytest.raises(ValueError):
                intent_language_data(MockAgentClass, FakeIntent)

# def test_intent_data_skips_private_folders():
#     ...

# def test_intent_data_rich_response_group():
#     ...

def test_session_parameters_with_custom_utterances_raise_exception():
    @dataclass
    class FakeIntentWithLanguage(FakeIntent):
        """It will inherit a required Session Parameter"""
    FakeIntentWithLanguage.__intent_language_data__ = mock_language_data(
        FakeIntentWithLanguage,
        ["Any example should raise an error"],
        ["Fake response"],
        LanguageCode.ENGLISH
    )

    print(FakeIntentWithLanguage.parameter_schema.session_parameters)

    with pytest.raises(ValueError):
        intent_language_data(None, FakeIntentWithLanguage, LanguageCode.ENGLISH)
