from typing import Type
from unittest.mock import patch
from dataclasses import dataclass

import pytest

from intents import Intent, Entity, Agent, LanguageCode
from intents.language import EntityEntry
from intents.connectors._experimental.alexa import language

def _get_toy_agent() -> Type[Agent]:
    class ToyAgent(Agent):
        languages = ['en', 'it']
    return ToyAgent

class ToyEntity(Entity):
    __entity_language_data__ = {
        LanguageCode.ENGLISH: [
            EntityEntry("*", ["multiplication", "asterisk"]), # invalid, but synonyms
            EntityEntry("plus", ['+']),
            EntityEntry("$$$", ['cash', 'money']),
        ],
        LanguageCode.ITALIAN: [
            EntityEntry("*", ["moltiplicazione", "per"]), # invalid, but synonyms
            EntityEntry("addizione", ['+', "più"]), # TODO: canonical value = "più"
            EntityEntry("$$$", ['cash', 'soldi']),
        ]
    }

@dataclass
class ToyIntent(Intent):
    foo: ToyEntity

class ToyInvalidEntity(Entity):
    __entity_language_data__ = {
        LanguageCode.ENGLISH: [
            EntityEntry("this", ['is', 'ok']),
            EntityEntry("not ok: *", []),
            EntityEntry("this", ['also', 'good']),
        ],
        LanguageCode.ITALIAN: [
            EntityEntry("questa", ['è', 'ok']),
            EntityEntry("non ok: *", []),
            EntityEntry("questa", ['anche', 'bene']),
        ]
    }

@dataclass
class ToyInvalidIntent(Intent):
    bar: ToyInvalidEntity

@patch('intents.language.intent_language_data')
def test_language_data_only_one_language(*args):
    ToyAgent = _get_toy_agent()
    ToyAgent.register(ToyIntent)
    lc = language.AlexaLanguageComponent(ToyAgent)
    language_data = lc.entity_language_data(ToyEntity, LanguageCode.ITALIAN)
    assert list(language_data.keys()) == [LanguageCode.ITALIAN]

@patch('intents.language.intent_language_data')
def test_language_data_removes_invalid(*args):
    ToyAgent = _get_toy_agent()
    ToyAgent.register(ToyIntent)
    lc = language.AlexaLanguageComponent(ToyAgent)
    language_data = lc.entity_language_data(ToyEntity)

    expected_english = [
        language.AlexaEntityEntry(
            value="*", synonyms=["multiplication", "asterisk"],
            alexa_value="multiplication", alexa_synonyms=["asterisk"]
        ),
        language.AlexaEntityEntry(
            value="plus", synonyms=["+"],
            alexa_value="plus", alexa_synonyms=[]
        ),
        language.AlexaEntityEntry(
            value="$$$", synonyms=["cash", "money"],
            alexa_value="cash", alexa_synonyms=["money"]
        ),
    ]
    assert language_data[LanguageCode.ENGLISH] == expected_english

    expected_italian = [
        language.AlexaEntityEntry(
            value="*", synonyms=["moltiplicazione", "per"],
            alexa_value="moltiplicazione", alexa_synonyms=["per"]
        ),
        language.AlexaEntityEntry(
            value="addizione", synonyms=['+', "più"],
            alexa_value="addizione", alexa_synonyms=[]
        ),
        language.AlexaEntityEntry(
            value="$$$", synonyms=["cash", "soldi"],
            alexa_value="cash", alexa_synonyms=["soldi"]
        ),
    ]
    assert language_data[LanguageCode.ITALIAN] == expected_italian

@patch('intents.language.intent_language_data')
def test_id_to_value(*args):
    ToyAgent = _get_toy_agent()
    ToyAgent.register(ToyIntent)

    lc = language.AlexaLanguageComponent(ToyAgent)

    assert len(lc._entry_id_to_value[LanguageCode.ENGLISH]) == len(ToyEntity.__entity_language_data__[LanguageCode.ENGLISH])
    assert len(lc._entry_id_to_value[LanguageCode.ITALIAN]) == len(ToyEntity.__entity_language_data__[LanguageCode.ITALIAN])
    assert lc.alexa_entry_id_to_value("ToyEntity-multiplication", LanguageCode.ENGLISH) == "*"
    assert lc.alexa_entry_id_to_value("ToyEntity-moltiplicazione", LanguageCode.ITALIAN) == "*"

@patch('intents.language.intent_language_data')
def invalid_entities_raise_error(*args):
    ToyAgent = _get_toy_agent()
    ToyAgent.register(ToyInvalidIntent)

    with pytest.raises(ValueError):
        language.AlexaLanguageComponent(ToyAgent)
