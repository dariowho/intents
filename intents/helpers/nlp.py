from typing import Union, Dict, List

from intents import LanguageCode

_WITH = {"it": " con ", "en": " with "}
_WITHOUT = {"it": " senza ", "en": " without "}
_AND = {"it": " e ", "en": " and "}

def render_list(string_list: List[str], language: Union[LanguageCode, str]="en") -> str:
    """
    >>> render_list(["one", "two", "three"], "en")
    "one, two and three"
    """
    language = LanguageCode.ensure(language)
    if len(string_list) == 0:
        return ""

    if len(string_list) == 1:
        return string_list[0]

    and_word = _AND.get(language.value, ", ")
    return ", ".join(string_list[:-1]) + and_word + string_list[-1]

def render_with(something: str, something_else: str, language: Union[LanguageCode, str]) -> str:
    """
    >>> render_with("royale", "cheese", "en")
    "royale with cheese"
    """
    language = LanguageCode.ensure(language)
    with_word = _WITH.get(language.value, ", ")
    return f"{something}{with_word}{something_else}"

def render_without(something: str, something_else: str, language: Union[LanguageCode, str]) -> str:
    """
    >>> render_without("royale", "cheese", "en")
    "royale without cheese"
    """
    language = LanguageCode.ensure(language)
    without_word = _WITHOUT.get(language.value, ", ")
    return f"{something}{without_word}{something_else}"
