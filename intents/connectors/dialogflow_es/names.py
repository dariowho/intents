from intents.types import IntentType

def context_name(intent_cls: IntentType) -> str:
    return "c_" + intent_cls.name.replace(".", "_") # TODO: refine

def event_name(intent_cls: IntentType) -> str:
    """
    Generate the default event name that we associate with every intent.

    >>> event_name('test.intent_name')
    'E_TEST_INTENT_NAME'
    """
    return "E_" + intent_cls.name.upper().replace('.', '_')