"""
This is the client-facing part of the interface. you will subclass the
:class:`Connector` base class, and clients will operate on its instances.
"""

import logging
from uuid import uuid1
from abc import ABC, abstractmethod
from typing import Union

from intents import Intent, Agent, LanguageCode
from intents.language import ensure_language_code, agent_supported_languages
from intents.connectors.interface.prediction import Prediction
from intents.connectors.interface.fulfillment import FulfillmentRequest

logger = logging.getLogger(__name__)

class Connector(ABC):
    """
    Connect the given Agent to a Prediction Service.

    Args:
        agent_cls: The Agent to connect
        default_session: A default session ID (conversation channel) for
            predictions. If None, Connector will generate a random string
        default_language: A default language for predictions. If None, Connector
            will use the Agent's firs defined language.
    """
    agent_cls: type(Agent)
    default_session: str
    default_language: str

    def __init__(
        self,
        agent_cls: type(Agent),
        default_session: str=None,
        default_language: Union[LanguageCode, str]=None
    ):
        if not default_language:
            default_language = agent_supported_languages(agent_cls)[0]
        default_language = ensure_language_code(default_language)
        
        if not default_session:
            default_session = f"py-{str(uuid1())}"
        
        self.agent_cls = agent_cls
        self.default_session = default_session
        self.default_language = default_language

    @abstractmethod
    def predict(self, message: str, session: str=None, language: Union[LanguageCode, str]=None) -> Prediction:
        """
        Predict the given User message in the given session using the given
        language. When `session` or `language` are None, `predict` will use the
        default values that are specified in :meth:`__init__`.

        *predict* will return an instance of :class:`Prediction`, representing
        the service response.

        >>> from intents.connectors import DialogflowEsConnector
        >>> from example_agent import ExampleAgent
        >>> df = DialogflowEsConnector('/path/to/service-account.json', ExampleAgent)
        >>> prediction = df.predict("Hi, my name is Guido")
        >>> prediction.intent
        UserNameGive(user_name='Guido')
        >>> prediction.intent.user_name
        "Guido"
        >>> prediction.fulfillment_text
        "Hi Guido, I'm Bot"
        >>> prediction.confidence
        0.86

        Args:
            message: The User message to predict
            session: Any string identifying a conversation
            language: A LanguageCode object, or a ISO 639-1 string (e.g. "en")
        """

    @abstractmethod
    def trigger(self, intent: Intent, session: str=None, language: Union[LanguageCode, str]=None) -> Prediction:
        """
        Trigger the given Intent in the given session using the given language.
        When `session` or `language` are None, `predict` will use the default
        values that are specified in :meth:`__init__`.

        >>> from intents.connectors import DialogflowEsConnector
        >>> from example_agent import ExampleAgent, smalltalk
        >>> df = DialogflowEsConnector('/path/to/service-account.json', ExampleAgent)
        >>> prediction = df.trigger(smalltalk.AgentNameGive(agent_name='Alice'))
        >>> prediction.intent
        AgentNameGive(agent_name='Alice')
        >>> prediction.fulfillment_text
        "Howdy Human, I'm Alice"
        >>> prediction.confidence
        1.0

        Args:
            intent: The Intent instance to trigger
            session: Any string identifying a conversation
            language: A LanguageCode object, or a ISO 639-1 string (e.g. "en")
        """

    @abstractmethod
    def fulfill(self, fulfillment_request: FulfillmentRequest) -> dict:
        """
        This method is responsible for handling requests coming from a
        fulfillment interface. We are at that point in the flow when an intent
        was triggered/predicted, and Service is calling the webhook service for
        fulfillment. Refer to :mod:`intents.fulfillment` for a more detailed
        explanation.

        In this method, Connector interprets the body of the request, builds a
        :class:`~intents.model.intent.FulfillmentContext` object, builds
        the :class:`~intents.model.Intent` object that is references in the
        request, and calls its :meth:`~intents.model.intent.Intent.fulfill`
        method.

        This will produce a
        :class:`~intents.model.intent.FulfillmentResult` object, that
        Connector will translate into a Service-compatible response (a
        dictionary) and return to caller.

        Args:
            fulfillment_request: A raw fulfillment request, as it is sent by the
                Prediction service (typically via a standard REST webhook call)
        Returns:
            An object containing a response that Service can read
        """

    @abstractmethod
    def upload(self):
        """
        Upload the connected Agent to the Prediction Service.
        """

    @abstractmethod
    def export(self, destination: str):
        """
        Export the connected Agent in a format that can be read and imported
        natively by the Prediction service. For instance, the Dialogflow service
        will produce a ZIP export that can be imported from the Dialogflow
        console.

        Note that you can also directly upload the Agent with :meth:`upload`.

        :param destination: destination path of the exported Agent
        """
