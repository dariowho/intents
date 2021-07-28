"""
The :class:`Agent` base class is the entry point of your project. You will
subclass it when defining your own Agent, and will later :meth:`Agent.register`
Intent classes and other resources into it.

Once the Agent is defined, you will connect it to a cloud service with a
:class:`Connector`, to make prediction and trigger requests.
"""
import re
import logging
import inspect
from types import ModuleType
from typing import List, Dict, Union
from dataclasses import dataclass

from intents.model.intent import Intent, _IntentMetaclass, IntentParameterMetadata
from intents.model.entity import EntityMixin, SystemEntityMixin, _EntityMetaclass
from intents.model.context import Context, _ContextMetaclass
from intents.model.event import _EventMetaclass
from intents import language

logger = logging.getLogger(__name__)

@dataclass
class RegisteredParameter:
    """
    Agents register intent parameters. If two intents declare the same parameter
    name, they must also declare the same type for it. 
    """
    metadata: IntentParameterMetadata
    used_in: List[type(Intent)]

class _AgentMetaclass(type):

    languages: List[language.LanguageCode] = None

    def __new__(cls, name, bases, dct):
        result_cls = super().__new__(cls, name, bases, dct)
        
        if name == 'Agent':
            assert not bases
            return result_cls

        if not result_cls.languages:
            result_cls.languages = language.agent_supported_languages(result_cls)

        languages = []
        for lan in result_cls.languages:
            if isinstance(lan, language.LanguageCode):
                languages.append(lan)
            elif isinstance(lan, str):
                languages.append(language.LanguageCode(lan))
            else:
                raise ValueError(f"Unsupported language '{lan}' for Agent '{result_cls}'. Must be a value of 'intents.LanguageCode'")
        result_cls.languages = languages

        return result_cls

class Agent(metaclass=_AgentMetaclass):
    """
    As the name suggests, Agent is the base class that models an Agent
    definition within the *Intents* framework.

    Typically, you will define a single Agent class in your project, that could
    be as simple as this:

    .. code-block:: python

        from intents import Agent

        class MyAgent(Agent):
            \"\"\"A little docstring for your Agent\"\"\"

    You can optionally define the languages that you intend to support.
    *Intents* will look for language resources based on the `language` class
    variable:

    .. code-block:: python

        class MyAgent(Agent):
            \"\"\"A little docstring for your Agent\"\"\"
            languages = ["en", "it"]

    Languages are values from :class:`intents.language.LanguageCode`. If omitted,
    *Intents* will discover language resources by itself.

    You won't do much more with your *Agent* class, other than registering
    intents and resources with :meth:`Agent.register`, or passing it to a
    :class:`Connector` to make predictions.
    """

    languages: List[language.LanguageCode] = None

    intents: List[Intent] = None
    _intents_by_name: Dict[str, Intent] = None
    _intents_by_norm_name: Dict[str, Intent] = None # my_module.HelloWorld -> mymodulehelloworld
    _intents_by_event: Dict[str, Intent] = None
    _entities_by_name: Dict[str, _EntityMetaclass] = None
    _contexts_by_name: Dict[str, _ContextMetaclass] = None
    _events_by_name: Dict[str, _EventMetaclass] = None
    _parameters_by_name: Dict[str, RegisteredParameter] = None

    @classmethod
    def register(cls, resource: Union[_IntentMetaclass, ModuleType]):
        """
        Register the given resource in Agent. The resource could be:

        * An :class:`Intent`
        * A module. In this case, the module is scanned (non recursively) for
          Intents, and each Intent is added individually

        This is how you register a **single intent**:

        .. code-block:: python

            from intents import Agent, Intent

            class MyAgent(Agent):
                pass

            @dataclass
            class MyTestIntent(Intent):
                \"\"\"A little docstring for my Intent...\"\"\"
                a_parameter: Sys.Date
                another_parameter: Sys.Person

            MyAgent.register(MyTestIntent)

        Alternatively, you can register a **whole module** containing Intents.
        This is how you register all the intents that are defined in the
        `smalltalk` module of `example_agent`:

        .. code-block:: python

            from example_agent import smalltalk

            class MyAgent(Agent):
                pass

            MyAgent.register(smalltalk)

        Note that together with each Intent, the Agent will register all of its
        linked resources, such as Entities, Events and Contexts.

        :param resource: The resource to register (an Intent, or a module
                         containing Intents)
        """
        if isinstance(resource, _IntentMetaclass):
            cls._register_intent(resource)

        elif isinstance(resource, ModuleType):
            for member_name, member in inspect.getmembers(resource, inspect.isclass):
                if member.__module__ == resource.__name__ and issubclass(member, Intent):
                    cls._register_intent(member)

    @classmethod
    def _register_intent(cls, intent_cls: _IntentMetaclass):
        """
        Register a single intent in the Agent class and check that language data is
        present for all supported languages (examples and responses).
        """
        if not cls.intents or not cls._intents_by_name and not cls._intents_by_event:
            assert not cls.intents and not cls._intents_by_name and not cls._intents_by_event
            assert not cls._contexts_by_name and not cls._events_by_name
            cls.intents = []
            cls._intents_by_name = {}
            cls._intents_by_norm_name = {}
            cls._intents_by_event = {}
            cls._entities_by_name = {}
            cls._contexts_by_name = {}
            cls._events_by_name = {}
            cls._parameters_by_name = {}

        norm_name = Agent._norm_name(intent_cls.name)
        if cls._intents_by_norm_name.get(norm_name):
            raise ValueError(f"Another intent exists with an equivalent name to {intent_cls.name}" +
                f": {cls._intents_by_norm_name[norm_name]}")

        # TODO: check conflicting events
        # event_name = Agent._event_name(name)
        # if conflicting_intent := cls._intents_by_event.get(event_name):
        #     raise ValueError(f"Intent name {name} is ambiguous and clashes with {conflicting_intent} ('{conflicting_intent.metadata.name}')")

        language.intent_language_data(cls, intent_cls) # TODO: Agent languages only

        if intent_cls.input_contexts or intent_cls.output_contexts:
            logger.warning("Intent '%s' defines input/output contexts. The contexts API is " +
                "deprecated and will be removed in version 0.3 of Intents. Consider upgrading " +
                "your Intent classes to use relations instead (see the 'shop' module of Example" +
                "Agent for more details).", intent_cls.name)

        for context_cls in intent_cls.input_contexts:
            cls._register_context(context_cls)

        for context in intent_cls.output_contexts:
            cls._register_context(context)

        for event_cls in intent_cls.events:
            cls._register_event(event_cls, intent_cls)

        for param_name, param_metadata in intent_cls.parameter_schema.items():
            cls._register_parameter(param_metadata, intent_cls)
            cls._register_entity(param_metadata.entity_cls, param_name, intent_cls.name)

        cls.intents.append(intent_cls)
        cls._intents_by_name[intent_cls.name] = intent_cls
        cls._intents_by_norm_name[norm_name] = intent_cls
        cls._intents_by_event[intent_cls.events[0].name] = intent_cls

    @classmethod
    def _register_parameter(cls, param_meta: IntentParameterMetadata, intent_cls: type(Intent)):
        existing_param: RegisteredParameter = cls._parameters_by_name.get(param_meta.name)
        if not existing_param:
            cls._parameters_by_name[param_meta.name] = RegisteredParameter(
                metadata=param_meta,
                used_in=[intent_cls]
            )
            return

        if param_meta.entity_cls != existing_param.metadata.entity_cls:
            raise ValueError(f"Parameters with the same name must have the same type. Parameter '{param_meta.name}' " +
                f"is declared in Intent '{intent_cls.name}' with type '{param_meta.entity_cls}'; however, it was " +
                f"also declared in Intents '{existing_param.used_in}' with type '{existing_param.metadata.entity_cls}'")
                
        if param_meta.is_list and not existing_param.metadata.is_list:
            raise ValueError(f"Parameters with the same name must have the same type. Parameter '{param_meta.name}' " +
                f"is declared in Intent '{intent_cls.name}' as a List; however, it was also declared in Intents " +
                f"'{existing_param.used_in}' as not a List")

        existing_param.used_in.append(intent_cls)

    @classmethod
    def _register_entity(cls, entity_cls: _EntityMetaclass, parameter_name: str, intent_name: str):
        if not issubclass(entity_cls, EntityMixin):
            raise ValueError(f"Invalid type '{entity_cls}' for parameter '{parameter_name}' in Intent '{intent_name}': must be an Entity. Try system entities such as 'intents.Sys.Integer', or define your own custom entity.")

        if issubclass(entity_cls, SystemEntityMixin):
            return

        existing_cls = cls._entities_by_name.get(entity_cls.name)
        if not existing_cls:
            language.entity_language_data(cls, entity_cls) # Checks that language data is existing and consistent
            cls._entities_by_name[entity_cls.name] = entity_cls
            return

        if id(entity_cls) != id(existing_cls):
            existing_cls_path = f"{existing_cls.__module__}.{existing_cls.__qualname__}"
            entity_cls_path = f"{entity_cls.__module__}.{entity_cls.__qualname__}"
            raise ValueError(f"Two different Entity classes exist with the same name: '{existing_cls_path}' and '{entity_cls_path}'")

    @classmethod
    def _register_context(cls, context_obj_or_cls: Union[_ContextMetaclass, Context]):
        if isinstance(context_obj_or_cls, Context):
            context_cls = context_obj_or_cls.__class__
        elif inspect.isclass(context_obj_or_cls) and issubclass(context_obj_or_cls, Context):
            context_cls = context_obj_or_cls
        else:
            raise ValueError(f"Context {context_obj_or_cls} is not a Context instance or subclass")

        existing_cls = cls._contexts_by_name.get(context_cls.name)
        if not existing_cls:
            cls._contexts_by_name[context_cls.name] = context_cls
            return

        if id(context_cls) != id(existing_cls):
            existing_cls_path = f"{existing_cls.__module__}.{existing_cls.__qualname__}"
            context_cls_path = f"{context_cls.__module__}.{context_cls.__qualname__}"
            raise ValueError(f"Two different Context classes exist with the same name: '{existing_cls_path}' and '{context_cls_path}'")

    @classmethod
    def _register_event(cls, event_cls: _EventMetaclass, intent_cls: _IntentMetaclass):
        existing_cls = cls._events_by_name.get(event_cls.name)

        if not existing_cls:
            cls._events_by_name[event_cls.name] = event_cls
            cls._intents_by_event[event_cls.name] = intent_cls
            return

        if id(existing_cls) != id(event_cls):
            existing_cls_path = f"{existing_cls.__module__}.{existing_cls.__qualname__}"
            event_cls_path = f"{event_cls.__module__}.{event_cls.__qualname__}"
            raise ValueError(f"Two different Event classes exist with the same name: '{existing_cls_path}' and '{event_cls_path}'")

        # TODO: model different intents with same event and different input
        # context (ok) vs. different intents with same event and same input
        # context (not ok).
        existing_intent = cls._intents_by_event[event_cls.name]
        raise ValueError(f"Event '{event_cls.name}' is alreadt associated to Intent '{existing_intent}'. An Event can only be associated with 1 intent. (differenciation by input contexts is not supported yet)")

    def _pylint_hack(self):
        raise NotImplementedError()

    @staticmethod
    def _event_name(intent_name: str) -> str:
        """
        Generate the default event name that we associate with every intent.

        >>> _event_name('test.intent_name')
        'E_TEST_INTENT_NAME'

        TODO: This is only used in Dialogflow -> Deprecate and move to DialogflowConnector
        """
        return "E_" + intent_name.upper().replace('.', '_')

    @staticmethod
    def _norm_name(intent_name: str) -> str:
        return re.sub(r"[^a-z0-9]", "", intent_name.lower())
