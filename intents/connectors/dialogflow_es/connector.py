"""
Here we implement :class:`DialogflowEsConnector`, an implementation of
:class:`Connector` that allows Agents to operate on Dialogflow.
"""
import os
import logging
import tempfile
from typing import Set, Union, Iterable
from dataclasses import dataclass, field

import google.auth.credentials
from google.cloud.dialogflow_v2.types import TextInput, QueryInput, EventInput
from google.cloud.dialogflow_v2.services.sessions import SessionsClient
from google.cloud.dialogflow_v2.services.agents import AgentsClient
from google.cloud.dialogflow_v2.types import DetectIntentResponse, RestoreAgentRequest
from google.protobuf.json_format import MessageToDict

from intents import Agent, Intent
from intents.model.relations import related_intents
from intents.service_connector import Connector, Prediction, deserialize_intent_parameters
from intents.connectors.dialogflow_es.auth import resolve_credentials
from intents.connectors.dialogflow_es.util import dict_to_protobuf
from intents.connectors.dialogflow_es import entities as df_entities
from intents.connectors.dialogflow_es import export as df_export
from intents.connectors.dialogflow_es.response_format import intent_responses
from intents.connectors.commons import WebhookConfiguration

logger = logging.getLogger(__name__)

RICH_RESPONSE_PLATFORMS = ["telegram", "facebook", "slack", "line", "hangouts"]

# Dialogflow makes use of Protobuffer for its data structures, and protobuf may be
# tricky to deal with. For instance, `MessageToDict` will convert snake_case to
# lowerCamelCase, so API is documented snake_case, protobuf is snake_case,
# dialogflow results are camelCase, protobuf converted to dict is camelCase
# (unless you use a flag, in that case it could also be snake_case) 💀 This is one
# of the reasons this library exists.

@dataclass
class DialogflowPrediction(Prediction):
    """
    This is an implementation of :class:`Prediction` that comes from Dialogflow.
    It adds a `df_response` field, through which the full Dialogflow prediction
    payload can be accessed. Note that this is a tool for debugging: relying on
    Dialogflow data in your business logic is likely to make it harder to
    connect your Agent to different platforms.

    `DialogflowPredictions` are produced internally by
    :class:`DialogflowEsConnector`, and automatically used to instantiate
    Intents in :class:`DialogflowEsConnector.predict` and
    :class:`DialogflowEsConnector.trigger`. Probably you won't need to manually
    operate with Predictions.
    """
    df_response: DetectIntentResponse = field(default=False, repr=False)

class DialogflowEsConnector(Connector):
    """
    This is an implementation of :class:`Connector` that enables Agents to
    work as Dialogflow projects.

    An Agent can be connected to Dialogflow by providing its :class:`Agent`
    class and service account credentials for the the Google Cloud project
    that hosts the Dialogflow ES agent:

    .. code-block:: python

        from example_agent import ExampleAgent
        from intents.connectors import DialogflowEsConnector
        df = DialogflowEsConnector('/path/to/your/service-account-credentials.json', ExampleAgent)

    The Connector can now be used, mainly to

    * Export the Agent with :meth:`DialogflowEsConnector.export`
    * Predict an utterance with :meth:`DialogflowEsConnector.predict`
    * Trigger an Intent with :meth:`DialogflowEsConnector.trigger`

    :param google_credentials: Path to service account JSON credentials, or a Credentials object
    :param agent_cls: The Agent to connect
    :param default_session: An arbitrary string to identify the conversation during predictions. Will be generated randomly if None
    :param dedefault_language: Default language to use during predictions
    :param rich_platforms: Platforms to include when exporting Rich response messages
    :param webhook_configuration: Webhook connection parameters
    """
    entity_mappings = df_entities.MAPPINGS
    rich_platforms: Iterable[str]
    webhook_configuration: WebhookConfiguration

    _credentials: google.auth.credentials.Credentials
    _session_client: SessionsClient

    def __init__(
        self,
        google_credentials: Union[str, google.auth.credentials.Credentials],
        agent_cls: type(Agent),
        default_session: str=None,
        default_language: str="en",
        rich_platforms: Iterable[str]=("telegram",),
        webhook_configuration: WebhookConfiguration=None
    ):
        super().__init__(agent_cls, default_session=default_session,
                         default_language=default_language)
        self._credentials = resolve_credentials(google_credentials)
        assert all([p in RICH_RESPONSE_PLATFORMS for p in rich_platforms])
        self._session_client = SessionsClient(credentials=self._credentials)
        self.rich_platforms = rich_platforms
        self.webhook_configuration = webhook_configuration
        self._need_context_set: Set[type(Intent)] = _build_need_context_set(agent_cls)

    @property
    def gcp_project_id(self) -> str:
        """
        Return the Google Cloud Project ID that is associated with the current Connection
        """
        return self._credentials.project_id

    def export(self, destination: str):
        agent_name = 'py-' + self.agent_cls.__name__
        return df_export.export(self, destination, agent_name)

    def upload(self):
        agents_client = AgentsClient(credentials=self._credentials)
        with tempfile.TemporaryDirectory() as tmp_dir:
            export_path = os.path.join(tmp_dir, 'agent.zip')
            self.export(export_path)
            with open(export_path, 'rb') as f:
                agent_content = f.read()
            restore_request = RestoreAgentRequest(
                parent=f"projects/{self.gcp_project_id}",
                agent_content=agent_content
            )
            agents_client.restore_agent(request=restore_request)


    def predict(self, message: str, session: str = None, language: str = None) -> Intent:
        if not session:
            session = self.default_session
        if not language:
            language = self.default_language

        text_input = TextInput(text=message, language_code=language)
        query_input = QueryInput(text=text_input)
        session_path = self._session_client.session_path(
            self.gcp_project_id, session)
        df_result = self._session_client.detect_intent(
            session=session_path,
            query_input=query_input
        )
        df_response = df_result

        return self._df_response_to_prediction(df_response)

    def trigger(self, intent: Intent, session: str=None, language: str=None) -> Intent:
        if not session:
            session = self.default_session
        if not language:
            language = self.default_language

        intent_name = intent.name
        event_name = Agent._event_name(intent_name)
        event_parameters = {}
        for param_name, param_metadata in intent.parameter_schema.items():
            param_mapping = df_entities.MAPPINGS[param_metadata.entity_cls]
            if param_name in intent.__dict__:
                param_value = intent.__dict__[param_name]
                event_parameters[param_name] = param_mapping.to_service(param_value)

        logger.info("Triggering event '%s' in session '%s' with parameters: %s",
                    event_name, session, event_parameters)
        if not event_parameters:
            event_parameters = {}

        event_input = EventInput(
            name=event_name,
            parameters=dict_to_protobuf(event_parameters),
            language_code=language
        )
        query_input = QueryInput(event=event_input)
        session_path = self._session_client.session_path(
            self.gcp_project_id, session)
        result = self._session_client.detect_intent(
            session=session_path,
            query_input=query_input
        )
        df_response = result

        return self._df_response_to_prediction(df_response)

    def _df_response_to_prediction(self, df_response: DetectIntentResponse) -> DialogflowPrediction:
        return DialogflowPrediction(
            intent=self._df_response_to_intent(df_response),
            confidence=df_response.query_result.intent_detection_confidence,
            fulfillment_message_dict=intent_responses(df_response),
            fulfillment_text=df_response.query_result.fulfillment_text,
            df_response=df_response
        )

    def _df_response_to_intent(self, df_response: DetectIntentResponse) -> Intent:
        """
        Convert a Dialogflow prediction response into an instance of :class:`Intent`.
        """
        # TODO: response may be partial in case of slot-filling
        # TODO: fill related intents
        intent_name = df_response.query_result.intent.display_name
        intent_cls: Intent = self.agent_cls._intents_by_name.get(intent_name)
        if not intent_cls:
            raise ValueError(f"Prediction returned intent '{intent_name}', " +
                "but this was not found in Agent definition. Make sure to restore a latest " +
                "Agent export from `services.dialogflow_es.export.export()`. If the problem " +
                "persists, please file a bug on the Intents repository.")
        df_parameters = MessageToDict(df_response._pb.query_result.parameters)
        parameters_dict = deserialize_intent_parameters(df_parameters, intent_cls, self.entity_mappings)
        return intent_cls(**parameters_dict)

    def _intent_needs_context(self, intent: Intent) -> bool:
        return intent in self._need_context_set

    @staticmethod
    def _context_name(intent: Intent) -> str:
        return "c_" + intent.name.replace(".", "_") # TODO: refine


def _build_need_context_set(agent_cls: type(Agent)) -> Set[Intent]:
    """
    Return a list of intents that need to spawn a context, based on their
    relations:

    * If intent *B* follows intent *A*, then intent *A* needs to spawn a context
    """
    result = set()
    for intent in agent_cls.intents:
        related = related_intents(intent)
        for parent_intent in related.follow:
            result.add(parent_intent)
    return result
