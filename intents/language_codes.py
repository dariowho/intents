from enum import Enum
from typing import Union

class LanguageCode(Enum):

    ENGLISH = 'en'
    ENGLISH_US = 'en_US'
    ENGLISH_UK = 'en_UK'
    ITALIAN = 'it'
    SPANISH = 'es'
    SPANISH_SPAIN = 'es_ES'
    SPANISH_LATIN_AMERICA = 'es_LA'
    GERMAN = 'de'
    FRENCH = 'fr'
    DUTCH = 'nl'
    CHINESE = 'zh'
    CHINESE_PRC = 'zh_CN'
    CHINESE_HONG_KONG = 'zh_HK'

LANGUAGE_CODES = [x.value for x in LanguageCode]

FALLBACK_LANGUAGE = {
    LanguageCode.ENGLISH: [
        LanguageCode.ENGLISH_UK,
        LanguageCode.ENGLISH_US
    ],
    LanguageCode.ENGLISH_US: [
        LanguageCode.ENGLISH,
        LanguageCode.ENGLISH_UK
    ],
    LanguageCode.ENGLISH_UK: [
        LanguageCode.ENGLISH,
        LanguageCode.ENGLISH_US
    ],
    LanguageCode.ITALIAN: [],
    LanguageCode.SPANISH: [
        LanguageCode.SPANISH_LATIN_AMERICA
    ],
    LanguageCode.SPANISH_SPAIN: [
        LanguageCode.SPANISH,
        LanguageCode.SPANISH_LATIN_AMERICA
    ],
    LanguageCode.SPANISH_LATIN_AMERICA: [
        LanguageCode.SPANISH,
        LanguageCode.SPANISH_SPAIN
    ],
    LanguageCode.GERMAN: [],
    LanguageCode.FRENCH: [],
    LanguageCode.DUTCH: [],
    LanguageCode.CHINESE: [
        LanguageCode.CHINESE_PRC
    ],
    LanguageCode.CHINESE_PRC: [
        LanguageCode.CHINESE
    ],
    LanguageCode.CHINESE_HONG_KONG: []
}

def ensure_language_code(lang: Union[LanguageCode, str]) -> LanguageCode:
    """
    Make sure `lang` is a :class:`LanguageCode` value. If not, return
    `LanguageCode(lang)` (assuming it's a string).

    This is useful for user-facing methods, where input may be a language code
    or a string.

    Args:
        lang: An input language code
    Returns:
        A LanguageCode object representing `lang` 
    """
    if isinstance(lang, LanguageCode):
        return lang
    return LanguageCode(lang)
