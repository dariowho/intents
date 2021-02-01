import re
from typing import List, Dict
from dataclasses import dataclass

from dialogflow_agents.model.intent import Intent, IntentMetadata

class Agent:

    intents: List[Intent] = []
    _intents_by_name: Dict[str, Intent] = {}
    _intents_by_event: Dict[str, Intent] = {}

    _session = None

    def __init__(self, google_credentials: str, session: str):
        self._session = None

    @classmethod
    def intent(cls, name: str):
        """
        Returns a decorator for Intent subclasses that:

        1. Turns the Intent subclass into a `dataclass`
        1. Registers the intent in the Agent object
        1. Attach metadata to the decorated Intent class
        1. Check language data (examples and responses)

        .. code-block::python

            from dialogflow_agents import Agent, Intent

            agent = Agent(...)

            @agent.intent('my_test_intent_name')
            class my_test_intent(Intent):
                a_parameter: str
                another_parameter: str

        """
        if not cls.intents or not cls._intents_by_name and not cls._intents_by_event:
            assert not cls.intents and not cls._intents_by_name
            cls.intents = []
            cls._intents_by_name = {}
            cls._intents_by_event = {}

        name_is_valid, reason = _is_valid_intent_name(name)
        if not name_is_valid:
            raise ValueError(f"Invalid name {name}: {reason}")

        if cls._intents_by_name.get(name):
            raise ValueError(f"Another intent exists with name {name}: {cls._intents_by_name[name]}")
        
        event_name = _event_name(name)
        if conflicting_intent := cls._intents_by_event.get(event_name):
            raise ValueError(f"Intent name {name} is ambiguous and clashes with {conflicting_intent} ('{conflicting_intent.metadata.name}')")

        intent_metadata = IntentMetadata(
            name=name,
            input_contexts=[], # TODO: model
            output_contexts=[], # TODO: model
            events=[event_name] # TODO: handle additional Events
            # TODO: handle other metadata
        )

        def _result_decorator(decorated_cls):
            result = dataclass(decorated_cls)
            decorated_cls.metadata = intent_metadata
            cls.intents.append(result)
            cls._intents_by_name[name] = result
            cls._intents_by_event[event_name] = result
            from dialogflow_agents import language
            language.intent_language_data(cls, result) # Checks that language data is existing and consistent
            return result

        return _result_decorator

    def predict(self, message: str) -> Intent:
        """
        1. Load persisted session if necessary
        2. Send predict() request, with existing session contexts
        3. Return the right `Intent` subclass

        :param message: The message to be interpreted
        """
        df_response = {
            'queryResult': {
                "queryText": "predict a mock intent please",
                "parameters": {
                    "a_parameter": "foo",
                    "another_parameter": "42"
                },
                "intent": {
                    "name": "fake-full-path-intent-name",
                    "displayName": "test.intent"
                },
                "intentDetectionConfidence": 0.8
            },
            "outputContexts": []
        }

        intent_name = df_response['queryResult']['intent']['displayName']
        intent_class = self._intents_by_name[intent_name]
        return intent_class.from_df_response(df_response)

    def trigger(self, intent: Intent) -> Intent:
        """
        Trigger the given intent with the given parameters. Return another
        instance of the given Intent, where prediction details have been filled
        in from the response.

        >>> from example_agent.intents import smalltalk
        >>> df_result = agent.trigger(smalltalk.agent_name_give(agent_name='Alice'))
        >>> df_result.confidence
        1.0
        """
        return None
        # return test_intent({
        #     'confidence': 1.0,
        #     'parameters': {
        #         'a_parameter': 'foo',
        #         'another_parameter': 42
        #     },
        #     'contexts': []
        # })

    def save_session(self):
        """
        Store the current session (most importantly, the list of active
        contexts) to a persisted storage.
        """
        pass

    def load_session(self):
        """
        Load session information (most importantly, the list of active contexts),
        in a format that can be used by :meth:`Agent.predict` to restore the
        state before prediction.
        """
        pass

def _event_name(intent_name: str) -> str:
    """
    Generate the default event name that we associate with every intent.

    >>> _event_name('test.intent_name')
    'E_TEST_INTENT_NAME'

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
#
# Example code
#

# class TestAgent(Agent):
#     pass

# @TestAgent.intent('test.intent')
# class test_intent(Intent):
#     a_parameter: str
#     another_parameter: int

# agent = TestAgent(None, 'fake-session-id')
# agent.predict("predict a mock intent please")
