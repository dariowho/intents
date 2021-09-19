from typing import Type

from intents import Intent
from intents.helpers.misc import camel_to_snake_case

def context_name(intent_cls: Type[Intent]) -> str:
    return "c_" + camel_to_snake_case(intent_cls.name.replace(".", "_")) # TODO: refine

def event_name(intent_cls: Type[Intent]) -> str:
    """
    Generate the default event name that we associate with every intent.

    >>> event_name('test.intent_name')
    'E_TEST_INTENT_NAME'
    """
    return "E_" + camel_to_snake_case(intent_cls.name.replace(".", "_")).upper()
