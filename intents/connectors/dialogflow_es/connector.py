"""
Here we implement :class:`DialogflowEsConnector`, an implementation of
:class:`Connector` that allows Agents to operate on Dialogflow ES.
"""
import os
import json
import logging
import tempfile
from glob import glob
from collections import defaultdict
from dataclasses import dataclass, field
from typing import DefaultDict, List, Set, Dict, Union, Iterable, Type

import google.auth.credentials
from google.cloud.dialogflow_v2.types import TextInput, QueryInput, EventInput
from google.cloud.dialogflow_v2.services.sessions import SessionsClient
from google.cloud.dialogflow_v2.services.agents import AgentsClient
from google.cloud.dialogflow_v2 import types as pb

from intents import Agent, Intent, LanguageCode, FulfillmentContext, FulfillmentResult
import intents
from intents.model.intent import FulfillmentSession
from intents.model.relations import intent_relations
from intents.connectors.interface import Prediction, FulfillmentRequest, WebhookConfiguration, serialize_intent_parameters, deserialize_intent_parameters, TestableConnector, RecordedFulfillmentCall
from intents.connectors.dialogflow_es.auth import resolve_credentials
from intents.connectors.dialogflow_es.util import dict_to_protobuf
from intents.connectors.dialogflow_es import webhook
from intents.connectors.dialogflow_es import names as df_names
from intents.connectors.dialogflow_es import entities as df_entities
from intents.connectors.dialogflow_es import export as df_export
from intents.connectors.dialogflow_es.prediction import PredictionBody, DetectIntentBody, WebhookRequestBody, intent_responses

logger = logging.getLogger(__name__)

RICH_RESPONSE_PLATFORMS = ["telegram", "facebook", "slack", "line", "hangouts"]

# Dialogflow makes use of Protobuffer for its data structures, and protobuf may be
# tricky to deal with. For instance, `MessageToDict` will convert snake_case to
# lowerCamelCase, so API is documented snake_case, protobuf is snake_case,
# REST dialogflow results are camelCase, protobuf converted to dict is camelCase
# (unless you use a flag, in that case it could also be snake_case) 💀 This is one
# of the reasons this library exists.

@dataclass
class DialogflowPrediction(Prediction):
    """
    This is an implementation of :class:`~intents.connectors.interface.Prediction`
    that comes from Dialogflow. It adds a `df_response` field, through which the
    full Dialogflow prediction payload can be accessed. Note that this is a tool
    for debugging: relying on Dialogflow data in your business logic is likely
    to make it harder to connect your Agent to different platforms.

    `DialogflowPredictions` are produced internally by
    :class:`DialogflowEsConnector`, and are returned by its :meth:`~DialogflowEsConnector.predict` and
    :meth:`~DialogflowEsConnector.trigger` methods.

    Args:
        intent: An instance of the predicted Intent
        confidence: Dialogflow's confidence on its prediction
        fulfillment_messages: A map of Intent Responses, as they were
            returned by the Service
        fulfillment_text: A plain-text version of the response
        df_response: Raw Dialogflow response data. It is advisable not to rely
            on this is production, if you want to keep cross-service compatibility
    """
    df_response: DetectIntentBody = field(default=False, repr=False)

class CustomDialogflowEsIntent(str):
    """
    This just gives a name to the content of custom intent files. These intents
    can be optionally imported in the Agent, but cannot be used within the
    *Intents* framework
    """

class DialogflowEsConnector(TestableConnector):
    """
    This is an implementation of :class:`~intents.connectors.interface.Connector`
    that enables Agents to work as Dialogflow projects.

    An Agent can be connected to Dialogflow by providing its :class:`~intents.model.agent.Agent`
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

    A notable init parameter is `custom_intents`. This is a path to a folder
    that contains raw Dialogflow JSON intent files. They will uploaded, but
    their fulfillment will be ignored, and won't return an Intent class when
    predicted. They are useful to include placeholders for features that are not
    yet modelled in *Intents*, such as Location entities, or Google Assistant
    helper intent triggers. Note that this is **experimental** and may be changed in
    the future.

    Args:
        google_credentials: Path to service account JSON credentials, or a Credentials object
        agent_cls: The Agent to connect
        default_session: An arbitrary string to identify the conversation during
            predictions. If None, Connector will generate a random string
        default_language: Default language to use during predictions. If None, Connector
            will use the Agent's firs defined language.
        rich_platforms: Platforms to include when exporting Rich response messages
        webhook_configuration: Webhook connection parameters
        custom_intents: Path to a folder containing custom Dialogflow intents
            JSON files.
    """
    entity_mappings = df_entities.MAPPINGS
    rich_platforms: Iterable[str]
    webhook_configuration: WebhookConfiguration

    _credentials: google.auth.credentials.Credentials
    _session_client: SessionsClient
    _need_context_set: Set[Type[Intent]]
    _intents_by_context: Dict[str, Type[Intent]]
    _custom_intents_by_name: str

    recorded_fulfillment_calls: DefaultDict[str, List[RecordedFulfillmentCall]]

    def __init__(
        self,
        google_credentials: Union[str, google.auth.credentials.Credentials],
        agent_cls: Type[Agent],
        default_session: str=None,
        default_language: Union[LanguageCode, str]=None,
        rich_platforms: Iterable[str]=("telegram",),
        webhook_configuration: WebhookConfiguration=None,
        custom_intents: str=None
    ):
        super().__init__(agent_cls, default_session=default_session,
                         default_language=default_language)
        self._credentials = resolve_credentials(google_credentials)
        assert all([p in RICH_RESPONSE_PLATFORMS for p in rich_platforms])
        self._session_client = SessionsClient(credentials=self._credentials)
        self.rich_platforms = rich_platforms
        self.webhook_configuration = webhook_configuration
        self._need_context_set = _build_need_context_set(agent_cls)
        self._intents_by_context = _build_intents_by_context(agent_cls)
        self._custom_intents_by_name = _load_custom_intents(custom_intents)
        self.recorded_fulfillment_calls = defaultdict(list)

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
            restore_request = pb.RestoreAgentRequest(
                parent=f"projects/{self.gcp_project_id}",
                agent_content=agent_content
            )
            agents_client.restore_agent(request=restore_request)

    def predict(self, message: str, session: str = None, language: Union[LanguageCode, str] = None) -> DialogflowPrediction:
        if not session:
            session = self.default_session
        if not language:
            language = self.default_language

        language = LanguageCode.ensure(language)
        text_input = TextInput(text=message, language_code=language.value)
        query_input = QueryInput(text=text_input)
        session_path = self._session_client.session_path(
            self.gcp_project_id, session)
        df_result = self._session_client.detect_intent(
            session=session_path,
            query_input=query_input
        )
        df_response = DetectIntentBody(df_result)

        return self._df_body_to_prediction(df_response)

    def trigger(self, intent: Intent, session: str=None, language: Union[LanguageCode, str]=None) -> DialogflowPrediction:
        if not session:
            session = self.default_session
        if not language:
            language = self.default_language

        language = LanguageCode.ensure(language)
        event_name = df_names.event_name(intent.__class__)
        event_parameters = serialize_intent_parameters(intent, df_entities.MAPPINGS)

        logger.info("Triggering event '%s' in session '%s' with parameters: %s",
                    event_name, session, event_parameters)

        event_input = EventInput(
            name=event_name,
            parameters=dict_to_protobuf(event_parameters),
            language_code=language.value
        )
        query_input = QueryInput(event=event_input)
        session_path = self._session_client.session_path(
            self.gcp_project_id, session)
        df_result = self._session_client.detect_intent(
            session=session_path,
            query_input=query_input
        )
        df_response = DetectIntentBody(df_result)

        return self._df_body_to_prediction(df_response)

    def fulfill(self, fulfillment_request: FulfillmentRequest) -> dict:
        webhook_body = WebhookRequestBody(fulfillment_request.body)
        context = self._df_body_to_fulfillment_context(webhook_body)

        # TODO: check
        if (webhook_body.queryResult.queryText == "actions_intent_PERMISSION") and (location := webhook_body.has_location()):
            logger.info("Google returned location data. Fulfilling with 'Agent.handle_location()'")
            fulfillment_result = FulfillmentResult.ensure(self.agent_cls.handle_location(location))
        else:
            intent = self._df_body_to_intent(webhook_body)
            if not intent:
                if webhook_body.queryResult.intent.name in self._custom_intents_by_name:
                    logger.info("Skipping fulfillment for custom intent %s", webhook_body.queryResult.intent.name)
                else:
                    logger.warning("Received slot filling fulfillment call (intent=None). This is not supported yet")
                return {} # TODO: remove when partial predictions are implemented
            fulfillment_result = FulfillmentResult.ensure(intent.fulfill(context))
        
        # TestableConnector
        if self.is_recording_enabled:
            self.recorded_fulfillment_calls[context.session.id].append(
                RecordedFulfillmentCall(intent, context, fulfillment_result)
            )

        logger.debug("Returning fulfillment result: %s", fulfillment_result)
        if fulfillment_result:
            result = webhook.fulfillment_result_to_response(fulfillment_result, context)
            logger.debug("fulfillment result: %s", result)
            return result
        return {}

    def _df_body_to_fulfillment_context(self, df_body: WebhookRequestBody) -> FulfillmentContext:
        return FulfillmentContext(
            session=FulfillmentSession(df_body.session_id),
            confidence=df_body.queryResult.intentDetectionConfidence,
            fulfillment_messages=intent_responses(df_body),
            fulfillment_text=df_body.queryResult.fulfillmentText,
            language=LanguageCode(df_body.queryResult.languageCode)
        )

    def _df_body_to_prediction(self, df_body: DetectIntentBody) -> DialogflowPrediction:
        return DialogflowPrediction(
            intent=self._df_body_to_intent(df_body),
            confidence=df_body.queryResult.intentDetectionConfidence,
            fulfillment_messages=intent_responses(df_body),
            fulfillment_text=df_body.queryResult.fulfillmentText,
            df_response=df_body.detect_intent
        )

    def _df_body_to_intent(
        self,
        df_body: PredictionBody,
        build_related_cls: Type[Intent]=None,
        visited_intents: Set[Type[Intent]]=None
    ) -> Intent:
        """
        Convert a Dialogflow prediction response into an instance of
        :class:`Intent`.
        
        This method is recursive on intent relations. When an intent has a
        :meth:`~intents.model.relations.follow` field, that field must be filled
        with an instance of the followed intent; in this case
        :meth:`_df_body_to_intent` will call itself passing the parent intent
        class as `build_related_cls`, to force building that intent from the
        same `df_body`; contexts and parameters will be checked for consistency.

        Args:
            df_body: A Dialogflow Response
            build_related_cls: Force to build the related intent instead of
                the predicted one
            visited_intents: This is used internally to prevent recursion loops
        """
        if not visited_intents:
            visited_intents = set()

        if df_body.queryResult.intent.name in self._custom_intents_by_name:
            logger.info("DF body references a custom intent. Returning 'None'")
            return

        contexts, context_parameters = df_body.contexts()

        # Slot filling in progress
        # TODO: also check queryResult.cancelsSlotFilling
        # if "__system_counters__" in contexts:
        if not df_body.queryResult.allRequiredParamsPresent:
            logger.warning("Prediction doesn't have values for all required parameters. "
                           "Slot filling may be in progress, but this is not modeled yet: "
                           "Intent object will be None")
            return None

        if build_related_cls:
            # TODO: adjust lifespan
            intent_cls = build_related_cls
            df_parameters = {
                p_name: p.value for p_name, p in context_parameters.items() 
                if p_name in intent_cls.parameter_schema
            }
        else:
            intent_name = df_body.intent_name
            intent_cls: Intent = self.agent_cls._intents_by_name.get(intent_name)
            if not intent_cls:
                raise ValueError(f"Prediction returned intent '{intent_name}', " +
                    "but this was not found in Agent definition. Make sure to restore a latest " +
                    "Agent export from `services.dialogflow_es.export.export()`. If the problem " +
                    "persists, please file a bug on the Intents repository.")
            df_parameters = df_body.intent_parameters

        visited_intents.add(intent_cls)
        parameter_dict = deserialize_intent_parameters(df_parameters, intent_cls, self.entity_mappings)
        related_intents_dict = {}
        for rel in intent_relations(intent_cls).follow:
            if rel.target_cls in visited_intents:
                raise ValueError(f"Loop detected: {rel.target_cls} was already visited. Make sure "
                                 "your Agent has no circular dependencies")
            related_intent = self._df_body_to_intent(df_body, rel.target_cls, visited_intents)
            related_intent.lifespan = df_body.context_lifespans.get(df_names.context_name(rel.target_cls), 0)
            
            related_intents_dict[rel.field_name] = related_intent

        result = intent_cls(**parameter_dict, **related_intents_dict)
        result.lifespan = df_body.context_lifespans.get(df_names.context_name(intent_cls), 0)
        return result

    def _intent_needs_context(self, intent: Intent) -> bool:
        return intent in self._need_context_set

def _build_need_context_set(agent_cls: Type[Agent]) -> Set[Intent]:
    """
    Return a list of intents that need to spawn a context, based on their
    relations:

    * If intent *B* follows intent *A*, then intent *A* needs to spawn a context
    """
    result = set()
    for intent in agent_cls.intents:
        related = intent_relations(intent)
        for rel in related.follow:
            result.add(rel.target_cls)
    return result

def _build_intents_by_context(agent_cls: Type[Agent]) -> Dict[str, Type[Intent]]:
    result = {}
    for intent_cls in agent_cls.intents:
        context_name = df_names.context_name(intent_cls)
        if context_name in result:
            raise ValueError(f"Intents '{intent_cls.name}' and '{result[context_name].name}' " +
                "have ambiguous context name. This is a bug: please file an issue on the " +
                "Intents repo. Quick fix: change the name of one of the two intents.")
        result[context_name] = intent_cls
    return result

def _load_custom_intents(path: str) -> Dict[str, CustomDialogflowEsIntent]:
    """
    Scan a folder (non-recursively) for JSON files and return their content,
    assuming they are Dialogflow custom intents.

    Args:
        path: Path to the folder containig JSON files

    Returns:
        A map where the key is an intent name, and its value is the dict content
        of the intent
    """
    result = {}
    if path:
        for filename in glob(os.path.join(path, "*.json")):
            with open(filename, 'r') as f:
                intent_dict = json.load(f)
                result[intent_dict['name']] = CustomDialogflowEsIntent(json.dumps(intent_dict, indent=2))
    return result
