from enum import Enum

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
