import pytest
from unittest.mock import patch

from intents import LanguageCode
from intents.language.agent_language import match_agent_language

@patch("intents.language.agent_language.agent_supported_languages")
def test_match_agent_language__agent_has_language(m_supported_languages):
    m_supported_languages.return_value = [LanguageCode.ENGLISH, LanguageCode.ITALIAN]
    assert match_agent_language(None, LanguageCode.ITALIAN) == LanguageCode.ITALIAN

@patch("intents.language.agent_language.agent_supported_languages")
def test_match_agent_language__agent_has_fallback_language(m_supported_languages):
    m_supported_languages.return_value = [LanguageCode.ENGLISH, LanguageCode.ITALIAN]
    assert match_agent_language(None, LanguageCode.ENGLISH_US) == LanguageCode.ENGLISH

@patch("intents.language.agent_language.agent_supported_languages")
def test_match_agent_language__agent_has_no_language(m_supported_languages):
    m_supported_languages.return_value = [LanguageCode.ENGLISH, LanguageCode.ITALIAN]
    with pytest.raises(KeyError):
        match_agent_language(None, LanguageCode.CHINESE_HONG_KONG)
