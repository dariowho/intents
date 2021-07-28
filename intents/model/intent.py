"""
An **intent** is a categorical representation of the User intention in a single
conversation turn. For instance, utterances like "I want a pizza", "I'd like to
order a pizza" and such, could be mapped to a single `OrderPizza` intent.

Your agent will typically define a number of *intents*, representing all the
types of messages the Agent can understand and answer to. This is done by
defining :class:`Intent` sub-classes and their language resources (see
:mod:`intents.language`), and registering them to an :class:`intents.Agent`
class with :meth:`intents.Agent.register`.
"""

import re
import inspect
import logging
import dataclasses
from dataclasses import dataclass
from typing import List, Dict, Any, _GenericAlias

from intents.model import context, event, entity
from intents.helpers.data_classes import is_dataclass_strict

logger = logging.getLogger(__name__)

#
# Intent
#

@dataclass
class IntentParameterMetadata:
    name: str
    entity_cls: entity._EntityMetaclass
    is_list: bool
    required: bool
    default: Any

class CallableDict(dict):
    """
    This is a proxy to handle the deprecation of
    :meth:`Intent.parameter_schema`, which is now a property. Legacy code may
    still call it as a method (e.g. `hello_intent.parameter_schema()`), hence we
    need to support `__call__`, warning User to update his code (e.g. `hello_intent.parameter_schema`) 
    """

    def __call__(self):
        logger.warning("'Intent.parameter_schema()' is deprecated, and is now a property. Use 'Intent.parameter_schema` instead. Support will be removed in 0.3")
        return self

class _IntentMetaclass(type):

    name: str = None
    input_contexts: List[context._ContextMetaclass] = None
    output_contexts: List[context.Context] = None
    events: List[event.Event] = None # TODO: at some point this may contain strings

    def __new__(cls, name, bases, dct):
        result_cls = super().__new__(cls, name, bases, dct)

        # Do not process Intent base class
        if name == 'Intent':
            assert not bases
            return result_cls

        for base_cls in bases:
            if base_cls is not Intent:
                if not is_dataclass_strict(base_cls):
                    logger.warning("Intent '%s' is inheriting from non-dataclass '%s'. Did you forget the decorator?", result_cls, base_cls)

        if "name" not in result_cls.__dict__:
            result_cls.name = _intent_name_from_class(result_cls)

        check_intent_name(result_cls.name)

        if not result_cls.input_contexts:
            result_cls.input_contexts = []
        if not result_cls.output_contexts:
            result_cls.output_contexts = []

        # TODO: check that custom parameters don't overlap Intent fields
        # TODO: check language data
        # language.intent_language_data(cls, result) # Checks that language data is existing and consistent

        events = [_system_event(result_cls.name)]
        for event_cls in result_cls.__dict__.get('events', []):
            events.append(event_cls)
        result_cls.events = events

        return result_cls

    @property
    def parameter_schema(cls) -> Dict[str, IntentParameterMetadata]:
        """
        Return a dict representing the Intent parameter definition. A key is a
        parameter name, a value is a :class:`IntentParameterMetadata` object.

        TODO: consider computing this in metaclass to cache value and check types
        """
        if cls is Intent:
            return {}

        if not is_dataclass_strict(cls):
            logger.warning(f"{cls} is not a dataclass. This may cause unexpected behavior: consider adding a @dataclass decorator to your Intent class.")
            cls = dataclass(cls)

        result = {}
        for param_field in cls.__dataclass_fields__.values():
        # for param_field in cls.__dict__['__dataclass_fields__'].values():
            # List[...]
            if inspect.isclass(param_field.type) and issubclass(param_field.type, Intent):
                continue

            if isinstance(param_field.type, _GenericAlias):
                if param_field.type.__dict__.get('_name') != 'List':
                    raise ValueError(f"Invalid typing '{param_field.type}' for parameter '{param_field.name}'. Only 'List' is supported.")

                if len(param_field.type.__dict__.get('__args__')) != 1:
                    raise ValueError(f"Invalid List modifier '{param_field.type}' for parameter '{param_field.name}'. Must define exactly one inner type (e.g. 'List[Sys.Integer]')")
                
                # From here on, check the inner type (e.g. List[Sys.Integer] -> Sys.Integer)
                entity_cls = param_field.type.__dict__.get('__args__')[0]
                is_list = True
            else:
                entity_cls = param_field.type
                is_list = False

            if not issubclass(entity_cls, entity.EntityMixin):
                raise ValueError(f"Parameter '{param_field.name}' of intent '{cls.name}' is of type '{entity_cls}', which is not an Entity.")

            required = True
            default = None
            if not isinstance(param_field.default, dataclasses._MISSING_TYPE):
                required = False
                default = param_field.default
            if not isinstance(param_field.default_factory, dataclasses._MISSING_TYPE):
                required = False
                default = param_field.default_factory()

            if not required and is_list and not isinstance(default, list):
                raise ValueError(f"List parameter has non-list default value in intent {cls}: {param_field}")

            result[param_field.name] = IntentParameterMetadata(
                name=param_field.name,
                entity_cls=entity_cls,
                is_list=is_list,
                required=required,
                default=default
            )

        return CallableDict(result)

class Intent(metaclass=_IntentMetaclass):
    """
    Represents a predicted intent. This is also used as a base class for the
    intent classes that model a Dialogflow Agent in Python code.

    In its simplest form, an Intent can be defined as follows:

    .. code-block:: python

        from intents import Intent

        class UserSaysHello(Intent):
            \"\"\"A little docstring for my Intent\"\"\"

    *Intents* will then look for language resources in the folder where your
    Agent class is defined, and specifically in
    `language/<LANGUAGE-CODE>/smalltalk.user_says_hello.yaml`. Note that the
    name of the module where the Intent is defined (`smalltalk.py`) is used as a
    prefix. More details in :mod:`intents.language`.

    Intents can be more complex than this, for instance:

    .. code-block:: python

        from dataclasses import dataclass
        from intents import Intent, Sys

        @dataclass
        class UserSaysHello(Intent):
            \"\"\"A little docstring for my Intent\"\"\"

            user_name: Sys.Person

            name = "hello_custom_name"

    This Intent has a custom name, so it will appear as "hello_custom_name" when
    exported to Dialogflow, and its language file will just be
    `hello_custom_name.yaml`, without module prefix. See
    :func:`check_intent_name` for more details on the rules that intent names
    must follow.

    Most importantly, this intent has a `user_name` **parameter** of type
    :class:`Sys.Person` (check out :class:`intents.model.entity.Sys` for
    available system entities). With adequate examples in its language file, it
    will be able to match utterances like "Hello, my name is John", tagging
    "John" as an Entity. When a connector is instantiated, predictions will look
    like this:

    >>> predicted = connector.predict("My name is John")
    >>> predicted.intent
    user_says_hello(user_name="John")
    >>> predicted.intent.user_name
    "John"
    >>> predicted.fulfillment_text
    "Hi John, I'm Agent"

    .. warning::

        Parameter names are meant to be **unique** within an Agent. That is, the same parameter
        must always be defined with the same type. This is because 1) Some services (e.g. 
        `Alexa <https://developer.amazon.com/en-US/docs/alexa/custom-skills/create-the-interaction-model-for-your-skill.html#intent-slot-names>`_)
        require so. 2) Predictions overwrite parameters in context based on their name: better
        make sure they are compatible.

    Last, we notice the **@dataclass** decorator. We require it to be added
    explicitly, this way IDEs will recognize the Intent class as a dataclass and
    provide correct hints for names and types.
    """
    # TODO: check parameter names: no underscore, no reserved names, max length

    name: str = None
    input_contexts: List[context._ContextMetaclass] = None
    output_contexts: List[context.Context] = None
    events: List[event.Event] = None # TODO: at some point this may contain strings

    @property
    def parameter_schema(self) -> Dict[str, IntentParameterMetadata]:
        return self.__class__.parameter_schema

def check_intent_name(candidate_name):
    """
    Raise `ValueError` if the given Intent name is not a valid name. Valid names

    * Only contain letter, underscore (`_`) and period (`.`) characters
    * Start with a letter
    * Don't contain repeated underscores (e.g. `__`)
    * Don't start wit `i_`. This is a reserved prefix for *Intents* system
      intents
    
    Note that `Agent.register` will apply further checks to spot duplicate
    intent names. Note that names are case insensitive, and shouldn't overlap
    with parameter names. 
    """
    invalid_reason = None
    
    if re.search(r'[^a-zA-Z_\.]', candidate_name):
        invalid_reason = "must only contain letters, underscore or period"

    if candidate_name.startswith('.') or candidate_name.startswith('_'):
        invalid_reason = "must start with a letter"

    if "__" in candidate_name:
        invalid_reason = "must not contain __"

    if candidate_name.startswith("i_"):
        invalid_reason = "the 'i_' prefix is reserved for system intents"

    if invalid_reason:
        raise ValueError(f"Invalid intent name '{candidate_name}': {invalid_reason}. " +
            "If the issue is related to your class name or path you can either change names to " +
            "be compliant, or use a custom name by setting 'Intent.name' manually. See the " +
            "documentation at https://intents.readthedocs.io/ for more information on intent " +
            "naming rules.")

def _intent_name_from_class(intent_cls: _IntentMetaclass) -> str:
    full_name = f"{intent_cls.__module__}.{intent_cls.__name__}"
    if intent_cls.__module__.startswith("_"):
        full_name = intent_cls.__name__
    # full_name = re.sub(r"_+", "_", full_name)
    return ".".join(full_name.split(".")[-2:])

def _system_event(intent_name: str) -> str:
    """
    Generate the default event name that we associate with every intent.

    >>> _event_name('test.intent_name')
    'E_TEST_INTENT_NAME'
    """
    # TODO: This is only used in Dialogflow -> Deprecate and move to DialogflowConnector
    event_name = "E_" + intent_name.upper().replace('.', '_')
    return event.SystemEvent(event_name)
