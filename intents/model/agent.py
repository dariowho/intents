"""
Here we provide the :class:`Agent` base class. You will subclass it when
defining your own Agent.
"""

import re
import logging
from inspect import isclass
from typing import List, Dict, Union
from dataclasses import dataclass

from intents import language
from intents.model.intent import Intent, _IntentMetaclass
from intents.model.entity import EntityMixin, SystemEntityMixin, _EntityMetaclass
from intents.model.context import Context, _ContextMetaclass
from intents.model.event import _EventMetaclass

logger = logging.getLogger(__name__)

class Agent:
    """
    As the name suggests, Agent is the base class for your Agents
    project.

    TODO: Agents used to be instantiated with connection parameters to make
    predictions. This is no more the case: consider using Agent instances
    instead of passing `agent_cls` around
    """

    intents: List[Intent] = None
    _intents_by_name: Dict[str, Intent] = None
    _intents_by_event: Dict[str, Intent] = None
    _entities_by_name: Dict[str, _EntityMetaclass] = None
    _contexts_by_name: Dict[str, _ContextMetaclass] = None
    _events_by_name: Dict[str, _EventMetaclass] = None

    @classmethod
    def register_intent(cls, intent_cls: _IntentMetaclass):
        """
        Returns a decorator for Intent subclasses that:

        #. Turns the Intent subclass into a `dataclass`
        #. Registers the intent in the Agent object
        #. Check language data (examples and responses)

        .. code-block:: python

            class MyAgent(Agent):
                pass

            class my_test_intent(Intent):
                a_parameter: str
                another_parameter: str

            MyAgent.register_intent(my_test_intent)

        """
        if not cls.intents or not cls._intents_by_name and not cls._intents_by_event:
            assert not cls.intents and not cls._intents_by_name and not cls._intents_by_event
            assert not cls._contexts_by_name and not cls._events_by_name
            cls.intents = []
            cls._intents_by_name = {}
            cls._intents_by_event = {}
            cls._entities_by_name = {}
            cls._contexts_by_name = {}
            cls._events_by_name = {}

        if cls._intents_by_name.get(intent_cls.name):
            raise ValueError(f"Another intent exists with name {intent_cls.name}: {cls._intents_by_name[intent_cls.name]}")

        # TODO: check conflicting events
        # event_name = Agent._event_name(name)
        # if conflicting_intent := cls._intents_by_event.get(event_name):
        #     raise ValueError(f"Intent name {name} is ambiguous and clashes with {conflicting_intent} ('{conflicting_intent.metadata.name}')")

        for context_cls in intent_cls.input_contexts:
            cls._register_context(context_cls)

        for context in intent_cls.output_contexts:
            cls._register_context(context)

        for event_cls in intent_cls.events:
            cls._register_event(event_cls, intent_cls)

        for param_name, param_metadata in intent_cls.parameter_schema().items():
            cls._register_entity(param_metadata.entity_cls, param_name, intent_cls.name)

        cls.intents.append(intent_cls)
        cls._intents_by_name[intent_cls.name] = intent_cls
        cls._intents_by_event[intent_cls.events[0].name] = intent_cls

    @classmethod
    def _register_entity(cls, entity_cls: _EntityMetaclass, parameter_name: str, intent_name: str):
        if not issubclass(entity_cls, EntityMixin):
            raise ValueError(f"Invalid type '{entity_cls}' for parameter '{parameter_name}' in Intent '{intent_name}': must be an Entity. Try 'intents.Sys.Any' if you are unsure.")

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
        elif isclass(context_obj_or_cls) and issubclass(context_obj_or_cls, Context):
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

    def save_session(self):
        """
        Store the current session (most importantly, the list of active
        contexts) to a persisted storage.
        """
        raise NotImplementedError("Context persistence is unsupported yet")

    def load_session(self):
        """
        Load session information (most importantly, the list of active contexts),
        in a format that can be used by :meth:`Agent.predict` to restore the
        state before prediction.
        """
        raise NotImplementedError("Context persistence is unsupported yet")

    @staticmethod
    def _event_name(intent_name: str) -> str:
        """
        Generate the default event name that we associate with every intent.

        >>> _event_name('test.intent_name')
        'E_TEST_INTENT_NAME'

        TODO: This is only used in Dialogflow -> Deprecate and move to DialogflowConnector
        """
        return "E_" + intent_name.upper().replace('.', '_')

def _is_valid_intent_name(candidate_name):
    if re.search(r'[^a-zA-Z_\.]', candidate_name):
        return False, "must only contain letters, underscore or dot"

    if candidate_name.startswith('.') or candidate_name.startswith('_'):
        return False, "must start with a letter"

    if "__" in candidate_name:
        return False, "must not contain __"

    return True, None
