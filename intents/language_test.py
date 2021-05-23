import os
import tempfile
from unittest.mock import patch

from intents import Agent
from intents import language

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

class MockIntentClass:
    name: str = 'test_intent'

    @classmethod
    def parameter_schema(cls):
        return {}

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
            result = language.intent_language_data(MockAgentClass, MockIntentClass)

    assert language.LanguageCode.ENGLISH in result
    assert isinstance(result[language.LanguageCode.ENGLISH], language.IntentLanguageData)

    assert result[language.LanguageCode.ENGLISH].example_utterances == [
        language.ExampleUtterance("Hi", MockIntentClass),
        language.ExampleUtterance("Hello", MockIntentClass)
    ]
    assert result[language.LanguageCode.ENGLISH].slot_filling_prompts == {}
    assert result[language.LanguageCode.ENGLISH].responses == {
        language.IntentResponseGroup.DEFAULT: [
            language.TextIntentResponse(["Greetings, human :)", "Hi human!"])
        ]
    }

# def test_intent_data_skips_private_folders():
#     ...

# def test_intent_data_rich_response_group():
#     ...