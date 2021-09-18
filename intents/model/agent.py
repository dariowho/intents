"""
The :class:`Agent` base class is the entry point of your project. You will
subclass it when defining your own Agent, and will later :meth:`Agent.register`
Intent classes and other resources into it.

Once the Agent is defined, you will connect it to a cloud service with a
:class:`Connector`, to make prediction and trigger requests.
"""
import re
import logging
from types import ModuleType
from dataclasses import dataclass
from inspect import isclass, getmembers
from typing import List, Dict, Union, Set, Type

from intents import LanguageCode
from intents.model.intent import Intent, IntentParameterMetadata
from intents.model.entity import EntityMixin, SystemEntityMixin
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

class AgentType(type):

    languages: List[LanguageCode] = None

    intents: List[Intent] = None
    _intents_by_name: Dict[str, Intent] = None
    _intents_by_norm_name: Dict[str, Intent] = None # my_module.HelloWorld -> mymodulehelloworld
    _entities_by_name: Dict[str, Type[EntityMixin]] = None
    _parameters_by_name: Dict[str, RegisteredParameter] = None
    _referenced_sys_entities: Set[SystemEntityMixin] = None # All

    def __new__(cls, name, bases, dct):
        result_cls = super().__new__(cls, name, bases, dct)
        
        if name == 'Agent':
            assert not bases
            return result_cls

        if not result_cls.languages:
            result_cls.languages = language.agent_supported_languages(result_cls)

        languages = []
        for lan in result_cls.languages:
            if isinstance(lan, LanguageCode):
                languages.append(lan)
            elif isinstance(lan, str):
                languages.append(LanguageCode(lan))
            else:
                raise ValueError(f"Unsupported language '{lan}' for Agent '{result_cls}'. Must be a value of 'intents.LanguageCode'")
        result_cls.languages = languages

        return result_cls

class Agent(metaclass=AgentType):
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

    Languages are values from :class:`LanguageCode`. If omitted,
    *Intents* will discover language resources by itself.

    You won't do much more with your *Agent* class, other than registering
    intents and resources with :meth:`Agent.register`, or passing it to a
    :class:`Connector` to make predictions.
    """

    @classmethod
    def register(cls, resource: Union[Type[Intent], ModuleType]):
        """
        Register the given resource in Agent. The resource could be:

        * An :class:`~intents.model.intent.Intent`
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
        linked properties and resources, such as parameters and Entities.

        :param resource: The resource to register (an Intent, or a module
                         containing Intents)
        """
        if isclass(resource) and issubclass(resource, Intent):
            cls._register_intent(resource)

        elif isinstance(resource, ModuleType):
            for member_name, member in getmembers(resource, isclass):
                if member.__module__ == resource.__name__ and issubclass(member, Intent):
                    cls._register_intent(member)

    @classmethod
    def _register_intent(cls, intent_cls: Type[Intent]):
        """
        Register a single intent in the Agent class and check that language data is
        present for all supported languages (examples and responses).
        """
        if not cls.intents or not cls._intents_by_name:
            assert not cls.intents and not cls._intents_by_name
            cls.intents = []
            cls._intents_by_name = {}
            cls._intents_by_norm_name = {}
            cls._entities_by_name = {}
            cls._parameters_by_name = {}
            cls._referenced_sys_entities = set()

        norm_name = Agent._norm_name(intent_cls.name)
        if cls._intents_by_norm_name.get(norm_name):
            raise ValueError(f"Another intent exists with an equivalent name to {intent_cls.name}" +
                f": {cls._intents_by_norm_name[norm_name]}")

        language.intent_language_data(cls, intent_cls) # TODO: Agent languages only

        for param_name, param_metadata in intent_cls.parameter_schema.items():
            cls._register_parameter(param_metadata, intent_cls)
            cls._register_entity(param_metadata.entity_cls, param_name, intent_cls.name)

        cls.intents.append(intent_cls)
        cls._intents_by_name[intent_cls.name] = intent_cls
        cls._intents_by_norm_name[norm_name] = intent_cls

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
    def _register_entity(cls, entity_cls: Type[EntityMixin], parameter_name: str, intent_name: str):
        if not issubclass(entity_cls, EntityMixin):
            raise ValueError(f"Invalid type '{entity_cls}' for parameter '{parameter_name}' in Intent '{intent_name}': must be an Entity. Try system entities such as 'intents.Sys.Integer', or define your own custom entity.")

        if issubclass(entity_cls, SystemEntityMixin):
            cls._referenced_sys_entities.add(entity_cls)
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

    def _pylint_hack(self):
        raise NotImplementedError()

    @staticmethod
    def _norm_name(intent_name: str) -> str:
        return re.sub(r"[^a-z0-9]", "", intent_name.lower())
