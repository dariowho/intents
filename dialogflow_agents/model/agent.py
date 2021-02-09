import re
import logging
from uuid import uuid1
from typing import List, Dict, Union
from dataclasses import dataclass

import google.auth.credentials
from google.protobuf.json_format import MessageToDict
from google.cloud.dialogflow_v2.types import TextInput, QueryInput, EventInput
from google.cloud.dialogflow_v2.services.sessions import SessionsClient
from google.cloud.dialogflow_v2.types import DetectIntentResponse

from dialogflow_agents.model.intent import Intent, IntentMetadata, IntentMetaclass
from dialogflow_agents.model.entity import StringParameter
from dialogflow_agents.dialogflow_helpers.auth import resolve_credentials
from dialogflow_agents.dialogflow_format.util import dict_to_protobuf

logger = logging.getLogger(__name__)

class Agent:

    intents: List[Intent] = []
    _intents_by_name: Dict[str, Intent] = {}
    _intents_by_event: Dict[str, Intent] = {}

    _credentials: google.auth.credentials.Credentials = None
    _session: str = None

    def __init__(self, google_credentials: Union[str, google.auth.credentials.Credentials], session: str=None, language: str="en"):
        if not session:
            session = f"py-{str(uuid1())}"
        self._credentials = resolve_credentials(google_credentials)
        self._session = session
        self.language = language
        self._df_session_client = SessionsClient(credentials=self._credentials)

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
            for field in result.__dataclass_fields__.values():
                # TODO: support List
                if not issubclass(field.type, StringParameter):
                    raise ValueError(f"Invalid type '{field.type}' for parameter '{field.name}' in Intent '{name}': must be an Entity. Try 'sys.any()' from 'dialogflow_agents.system_entities' if you are unsure.")
            decorated_cls.metadata = intent_metadata
            cls.intents.append(result)
            cls._intents_by_name[name] = result
            cls._intents_by_event[event_name] = result
            from dialogflow_agents import language
            language.intent_language_data(cls, result) # Checks that language data is existing and consistent
            return result

        return _result_decorator

    @classmethod
    def _prediction_to_intent(cls, df_response: DetectIntentResponse) -> Intent:
        """
        Turns a Dialogflow response dict (note: no protobuf) into its Intent class.
        """
        intent_name = df_response.query_result.intent.display_name
        intent_class = cls._intents_by_name.get(intent_name)
        if not intent_class:
            raise ValueError(f"Dialogflow prediction returned intent '{intent_name}', but this was not found in Agent definition. Make sure to restore a latest Agent export from `dialogflow_format.export.export()`. If the problem persists, please file a bug on the Dialoglfow Agents repository.")
        return intent_class.from_df_response(df_response)

    @property
    def gcp_project_id(self):
        return self._credentials.project_id

    @property
    def name(self):
        return f"py-{self.gcp_project_id}"

    def predict(self, message: str) -> Intent:
        """
        1. Load persisted session if necessary
        2. Send predict() request, with existing session contexts
        3. Return the right `Intent` subclass

        :param message: The message to be interpreted
        """
        text_input = TextInput(text=message, language_code=self.language)
        query_input = QueryInput(text=text_input)
        session_path=self._df_session_client.session_path(self.gcp_project_id, self._session)
        df_result = self._df_session_client.detect_intent(
            session=session_path,
            query_input=query_input
        )
        df_response = df_result._pb
        return self._prediction_to_intent(df_response)

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
        intent_name = intent.metadata.name
        event_name = _event_name(intent_name)
        event_parameters = {}
        for parameter_name in intent.__dataclass_fields__:
            if parameter_name in intent.__dict__:
                event_parameters[parameter_name] = intent.__dict__[parameter_name]

        logger.info("Triggering event '%s' in session '%s' with parameters: %s", event_name, self._session, event_parameters)
        if not event_parameters:
            event_parameters = {}
            
        event_input = EventInput(
            name=event_name,
            parameters=dict_to_protobuf(event_parameters),
            language_code=self.language
        )
        query_input = QueryInput(event=event_input)
        session_path=self._df_session_client.session_path(self.gcp_project_id, self._session)
        result = self._df_session_client.detect_intent(
            session=session_path,
            query_input=query_input
        )
        df_response = result._pb
        return self._prediction_to_intent(df_response)

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

# from example_agent import ExampleAgent
# from example_agent.intents import smalltalk

# agent = ExampleAgent('/home/dario/lavoro/dialogflow-agents/_tmp_agents/learning-dialogflow-5827a2d16c34.json')
# triggered_intent = agent.trigger(smalltalk.agent_name_give(agent_name='Ugo'))
# predicted_intent = agent.predict("My name is Guido")
