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
import json
import http.server
from typing import List
from dataclasses import dataclass, field

from intents import LanguageCode
# from intents.language import LanguageCode, IntentResponse, IntentResponseDict

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
    fulfillment_messages: "intents.language.intent_language.IntentResponseDict"
    language: LanguageCode

@dataclass
class FulfillmentResult:
    """
    `FulfillmentResult` are produced by `~intents.model.intent.Intent.fulfill`,
    and then converted by Connectors into Service-actionable responses.
    """
    trigger: "intents.model.Intent" = None
    fulfillment_text: List[str] = None
    fulfillment_messages: List["intents.language.intent_language.IntentResponse"] = None

#
# Development Server
#
import json
import http.server

def run_dev_server(connector: "intents.service_connector.Connector", host='', port=8000):
    server_address = (host, port)

    class DevWebhookHttpHandler(http.server.BaseHTTPRequestHandler):

            def do_POST(self):
                print("rfile", self.rfile)
                content_len = int(self.headers.get('Content-Length'))
                post_body = self.rfile.read(content_len)
                post_body = json.loads(post_body)
                print("post_body", post_body)

                fulfillment_request = FulfillmentRequest(
                    body=post_body
                )
                result = connector.fulfill(fulfillment_request)
                result = json.dumps(result)
                # result = json.dumps({"foo": "bar"})
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                # self.send_response(http.server.HTTPStatus.OK, "intents ok")

                result = bytes(result, 'utf-8')
                self.wfile.write(result)
                self.wfile.flush()

    httpd = http.server.HTTPServer(('', 8000), DevWebhookHttpHandler)
    httpd.serve_forever()


# from example_agent import ExampleAgent
# from intents.connectors import DialogflowEsConnector, WebhookConfiguration
# df = DialogflowEsConnector(
#     '/home/dario/lavoro/dialogflow-agents/_tmp_agents/learning-dialogflow-5827a2d16c34.json',
#     ExampleAgent,
#     default_session='testing-session'
# )
# run_dev_server(df)
