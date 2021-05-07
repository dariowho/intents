"""
Here we implement :class:`DialogflowPredictionService`, the instance of
:class:`PredictionService` that allows Agents to operate on Dialogflow

Dialogflow makes use of Protobuffer for its data structures, and protobuf may be
tricky to deal with. For instance, `MessageToDict` will convert snake_case to
lowerCamelCase, so API is documented snake_case, protobuf is snake_case,
dialogflow results are camelCase, protobuf converted to dict is camelCase
(unless you use a flag, in that case it could also be snake_case) 💀 This is one
of the reasons this library exists.
"""
import logging
from typing import Union
from dataclasses import dataclass

import google.auth.credentials
from google.cloud.dialogflow_v2.types import TextInput, QueryInput, EventInput
from google.cloud.dialogflow_v2.services.sessions import SessionsClient
from google.cloud.dialogflow_v2.types import DetectIntentResponse
from google.protobuf.json_format import MessageToDict

from dialogflow_agents import Agent, Intent
from dialogflow_agents.prediction_service import PredictionService, Prediction, EntityMapping
from dialogflow_agents.model.intent import TextFulfillmentMessage
from dialogflow_agents.dialogflow_service.auth import resolve_credentials
from dialogflow_agents.dialogflow_service.util import dict_to_protobuf
from dialogflow_agents.dialogflow_service import entities as df_entities

logger = logging.getLogger(__name__)

@dataclass
class DialogflowPrediction(Prediction):
    """
    This is an implementation of :class:`Prediction` that comes from Dialogflow.
    `DialogflowPredictions` are produced by :class:`DialogflowPredictionService`
    """
    df_response: DetectIntentResponse = None

    entity_mappings = df_entities.MAPPINGS


class DialogflowPredictionService(PredictionService):
    """
    This is an implementation of :class:`PredictionService` that enable Agents to
    work as Dialogflow projects
    """

    entity_mappings = df_entities.MAPPINGS

    _agent: Agent

    _credentials: google.auth.credentials.Credentials
    _session_client: SessionsClient
    
    def __init__(self, agent: Agent, google_credentials: Union[str, google.auth.credentials.Credentials]):
        self._agent = agent
        self._credentials = resolve_credentials(google_credentials)
        self._session_client = SessionsClient(credentials=self._credentials)

    @property
    def gcp_project_id(self):
        return self._credentials.project_id

    def predict_intent(self, message: str) -> Prediction:
        text_input = TextInput(text=message, language_code=self._agent.language)
        query_input = QueryInput(text=text_input)
        session_path=self._session_client.session_path(self.gcp_project_id, self._agent._session)
        df_result = self._session_client.detect_intent(
            session=session_path,
            query_input=query_input
        )
        df_response = df_result._pb
        return _df_response_to_prediction(df_response)

    def trigger_intent(self, intent: Intent) -> Prediction:
        intent_name = intent.metadata.name
        event_name = Agent._event_name(intent_name)
        event_parameters = {}
        for parameter_name in intent.parameter_schema():
            if parameter_name in intent.__dict__:
                event_parameters[parameter_name] = intent.__dict__[parameter_name]

        logger.info("Triggering event '%s' in session '%s' with parameters: %s", event_name, self._agent._session, event_parameters)
        if not event_parameters:
            event_parameters = {}
            
        event_input = EventInput(
            name=event_name,
            parameters=dict_to_protobuf(event_parameters),
            language_code=self._agent.language
        )
        query_input = QueryInput(event=event_input)
        session_path=self._session_client.session_path(self.gcp_project_id, self._agent._session)
        result = self._session_client.detect_intent(
            session=session_path,
            query_input=query_input
        )
        df_response = result._pb

        return _df_response_to_prediction(df_response)

def _df_response_to_prediction(df_response: DetectIntentResponse) -> DialogflowPrediction:
    fulfillment_messages = []
    for message in df_response.query_result.fulfillment_messages:
        fulfillment_messages.append(_build_response_message(message))

    return DialogflowPrediction( # pylint: disable=abstract-class-instantiated
        intent_name=df_response.query_result.intent.display_name,
        parameters_dict=MessageToDict(df_response.query_result.parameters), # TODO: check types
        contexts=[MessageToDict(c) for c in df_response.query_result.output_contexts], # TODO: model
        confidence=df_response.query_result.intent_detection_confidence,
        fulfillment_messages=fulfillment_messages,
        fulfillment_text=df_response.query_result.fulfillment_text,
        df_response=df_response
    )

def _build_response_message(protobuf):
    """
    Build a fulfillment message from a protobuf structure, as it is found in a
    protobuf response (`query_result.fulfillment_messages`)
    """
    if protobuf.HasField('text'):
        return _build_text_fulfillment_message(protobuf)
    else:
        raise ValueError("Unsupported Fulfillment Message: %s", protobuf)

def _build_text_fulfillment_message(protobuf):
    """
    Build a Text Fulfillment Message from the protobuf equivalent of the
    following dict:

    ```
    {
        "text": {
            "text": [
                "Hello, Human"
            ]
        }
    }
    ```

    https://cloud.google.com/dialogflow/es/docs/reference/rpc/google.cloud.dialogflow.v2#text

    We ignore, the fact that `text` is defined as a list: Dialogflow responses
    only have one.
    """
    text_list = protobuf.text.text
    if len(text_list) == 0:
        return TextFulfillmentMessage('')
    if len(text_list) > 1:
        logger.warning('Text Dialogflow response contains more than one text option, only the first will be considered: %s', protobuf)
    return TextFulfillmentMessage(protobuf.text.text[0])
