"""
It is common for Intents to need some additional business logic to be fulfilled.
For instance, an intent like *"is it going to rain tomorrow?"* should call a
weather service of some sort in order to produce a response for a User.

This is typically achieved through fulfillment calls. Those are functions that
are called by the prediction service after an Intent is predicted, but before
returning the prediction to client, typically through a REST webhook call.

A fulfillment function may change the set of responses that will be sent to
User, as well as redirecting the whole prediction towards another intent. This
is the typical flow of a fulfillment request:

#. A prediction request is sent to Service, either from
   :meth:`~intents.service_connector.Connector.predict`, or through some native
   service integration (Dialogflow natively supports Telegram, Slack, and so on).
#. Service predicts an Intent and its parameter values
#. Service sends a fulfillment request to its configured endpoint
#. *Intents* fulfillment framework receives the reuest and builds a
:class:`FulfillmentRequest` object.
#. Fulfillment framework passes the :class:`FulfillmentRequest` object to the
:meth:`~intents.service_connector.Connector.fulfill` method of
:class:`:meth:`~intents.service_connector.Connector`.
#. Connector parses the fulfillment request, and builds both the Intent
object and a :class:`FulfillmentContext` object
#. Connector calls :meth:`~intents.model.intent.Intent.fulfill` on the intent object, passing the context
#. :meth:`~intents.model.intent.Intent.fulfill` returns :class:`FulfillmentResult`
#. Connector builds the fulfillment response, in a format that Service can understand
#. Connector returns the response to the fulfillment framework
#. Fulfillment framework returns the Connector's response 
"""
from typing import List
from dataclasses import dataclass, field

from intents import Intent
from intents.language import LanguageCode, IntentResponse, IntentResponseDict

@dataclass
class FulfillmentRequest:
    """
    The purpose of this class is to uniform fulfillment request payloads, with
    respect to the protocol or framework they are sent with (REST, websocket,
    lambda, ...) 

    Note that the actual parsing comes later, when a :class:`Connector` receives
    the Request, and models it as a :class:`FulfillmentContext`.

    Also, it is not necessary to model a `FulfillmentResponse` counterpart: we
    can assume any fulfillment response can be modeled with a JSON-serializable
    dict.
    """
    body: dict
    headers: dict = field(default_factory=dict)

@dataclass
class FulfillmentContext:
    """
    `FulfillmentContext` objects are produced by Connectors and fed to the
    :meth:`~intents.model.intent.Intent.fulfill` method of
    :class:`~intents.model.intent.Intent` classes.
    """
    confidence: float
    fulfillment_text: str
    fulfillment_messages: IntentResponseDict
    language: LanguageCode

@dataclass
class FulfillmentResult:
    """
    `FulfillmentResult` are produced by `~intents.model.intent.Intent.fulfill`,
    and then converted by Connectors into Service-actionable responses.
    """
    replace_intent: Intent = None
    fulfillment_messages: List[IntentResponse] = None
    fulfillment_text: List[str] = None
