"""
Here we implement :class:`DialogflowEsConnector`, the implementation of
:class:`ServiceConnector` that allows Agents to operate on Dialogflow.
"""
import logging
from dataclasses import dataclass
from typing import Union, Iterable

import google.auth.credentials
from google.cloud.dialogflow_v2.types import TextInput, QueryInput, EventInput
from google.cloud.dialogflow_v2.services.sessions import SessionsClient
from google.cloud.dialogflow_v2.types import DetectIntentResponse
from google.protobuf.json_format import MessageToDict

from intents import Agent, Intent
from intents.service_connector import ServiceConnector, Prediction
from intents.services.dialogflow_es.auth import resolve_credentials
from intents.services.dialogflow_es.util import dict_to_protobuf
from intents.services.dialogflow_es import entities as df_entities
from intents.services.dialogflow_es import export as df_export
from intents.services.dialogflow_es.response_format import build_response_message

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
    `DialogflowPredictions` are produced internally by :class:`DialogflowEsConnector`
    """
    df_response: DetectIntentResponse = None

    entity_mappings = df_entities.MAPPINGS


class DialogflowEsConnector(ServiceConnector):
    """
    This is an implementation of :class:`ServiceConnector` that enable Agents to
    work as Dialogflow projects
    """

    entity_mappings = df_entities.MAPPINGS
    rich_platforms: Iterable[str]

    _credentials: google.auth.credentials.Credentials
    _session_client: SessionsClient

    def __init__(
        self,
        google_credentials: Union[str, google.auth.credentials.Credentials],
        agent_cls: type(Agent),
        default_session: str = None,
        default_language: str = "en",
        rich_platforms: Iterable[str] = ("telegram",)
    ):
        """
        :param google_credentials: Path to service account JSON credentials, or
        a Credentials object
        :param agent_cls: The Agent to connect
        :param default_session: An arbitrary string to identify the conversation
        during predictions. Will be generated randomly if None
        :param dedefault_language: Default language to use during predictions
        :param rich_platforms: Platforms to include when exporting Rich response messages
        """
        super().__init__(agent_cls, default_session=default_session,
                         default_language=default_language)
        self._credentials = resolve_credentials(google_credentials)
        self._session_client = SessionsClient(credentials=self._credentials)
        assert all([p in RICH_RESPONSE_PLATFORMS for p in rich_platforms])
        self.rich_platforms = rich_platforms

    @property
    def gcp_project_id(self) -> str:
        """
        Return the Google Cloud Project ID that is associated with the current Connection
        """
        return self._credentials.project_id

    def export(self, destination: str):
        agent_name = 'py-' + self.agent_cls.__name__
        return df_export.export(self, destination, agent_name)

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
        
        prediction = _df_response_to_prediction(df_response)
        return self._prediction_to_intent(prediction)

    def trigger(self, intent: Intent, session: str=None, language: str=None) -> Intent:
        if not session:
            session = self.default_session
        if not language:
            language = self.default_language

        intent_name = intent.name
        event_name = Agent._event_name(intent_name)
        event_parameters = {}
        for parameter_name in intent.parameter_schema():
            if parameter_name in intent.__dict__:
                event_parameters[parameter_name] = intent.__dict__[
                    parameter_name]

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

        prediction = _df_response_to_prediction(df_response)
        return self._prediction_to_intent(prediction)

    def _prediction_to_intent(self, prediction: Prediction) -> Intent:
        """
        Turns a Prediction object into an Intent object
        """
        intent_class: Intent = self.agent_cls._intents_by_name.get(prediction.intent_name)
        if not intent_class:
            raise ValueError(f"Prediction returned intent '{prediction.intent_name}', but this was not found in Agent definition. Make sure to restore a latest Agent export from `services.dialogflow_es.export.export()`. If the problem persists, please file a bug on the Intents repository.")
        return intent_class.from_prediction(prediction)

#
# Response to prediction
#

def _df_response_to_prediction(df_response: DetectIntentResponse) -> DialogflowPrediction:
    fulfillment_messages = []
    for message in df_response.query_result.fulfillment_messages:
        fulfillment_messages.append(build_response_message(message))

    return DialogflowPrediction(  # pylint: disable=abstract-class-instantiated
        intent_name=df_response.query_result.intent.display_name,
        parameters_dict=MessageToDict(
            df_response.query_result.parameters),  # TODO: check types
        # TODO: model
        contexts=[MessageToDict(c)
                  for c in df_response.query_result.output_contexts],
        confidence=df_response.query_result.intent_detection_confidence,
        fulfillment_messages=fulfillment_messages,
        fulfillment_text=df_response.query_result.fulfillment_text,
        df_response=df_response
    )
