"""
It is common for Intents to need some additional business logic to be fulfilled.
For instance, an intent like *"is it going to rain tomorrow?"* should call a
weather service of some sort in order to produce a response.

This is typically achieved through fulfillment calls. Those are functions that
are called by the prediction service after an Intent is predicted, but before
returning the prediction to client, typically through a **REST webhook call**.
Their purpose is to run some logic and optionally change the default Intent
response.

:class:`~intents.model.intent.Intent` classes may override their
:meth:`~intents.model.intent.Intent.fulfill` method to specify the behavior for
fulfillment calls:

.. code-block:: python

    @dataclass
    class UserAsksRain(Intent):
        \"\"\"Is it going to rain tomorrow?\"\"\"
        when: Sys.Date

        def fulfill(self, context: FulfillmentContext, **kwargs) -> Intent:
            result = wheather_api.get_wheather(date=self.when)
            if result == 'rain':
                return AgentReportsRainyWheather()
            else:
                return AgentReportsGoodWeather()

Connectors are responsible for receiving fulfillment requests from Services,
build the appropriate :class:`~intents.model.intent.Intent` instance, and call
:meth:`~intents.model.intent.Intent.fulfill` on it. We notice that
:meth:`~intents.model.intent.Intent.fulfill` returns
:class:`~intents.model.intent.Intent` instances. These are used to trigger a new
intent, that will produce the response. Return `None` if you do not wish to
change the Intent default response.

.. note::

    It is common for platforms to allow fulfillment calls to just produce a set
    of responses as a fulfillment result, without triggering a whole other intent.
    However, for now only triggers are supported, as they are the most general case.
    This may change in next releases.

Fulfillment flow
================
This is the typical flow of a fulfillment request:

#. A prediction request is sent to Service, either from
   :meth:`~intents.service_connector.Connector.predict`, or through some native
   service integration (Dialogflow natively supports Telegram, Slack, and so on).
#. Service predicts an Intent and its parameter values
#. Service sends a fulfillment request to its configured endpoint (that's us)
#. *Intents* fulfillment framework receives the reuest and builds a
   :class:`FulfillmentRequest` object.
#. Fulfillment framework passes the :class:`FulfillmentRequest` object to the
   :meth:`~intents.service_connector.Connector.fulfill` method of
   :class:`~intents.service_connector.Connector`.
#. Connector parses the fulfillment request, and builds both the Intent
   object and a :class:`~intents.model.intent.FulfillmentContext` object
#. Connector calls :meth:`~intents.model.intent.Intent.fulfill` on the intent object, passing the context
#. :meth:`~intents.model.intent.Intent.fulfill` runs its business logic, and
   optionally return another intent to trigger
#. Connector builds the fulfillment response, in a format that Service can understand
#. Connector returns the response to the fulfillment framework
#. Fulfillment framework returns the Connector's response

Serving
=======

The flow above requires you to serve an endpoint that Service can call. For
development you can use the included **development server** (more details at
:func:`run_dev_server`).

For production you must write your own; this is supposed to be fairly simple:
only thing your endpoint should do is to build a :class:`FulfillmentRequest`
object out of request data, and call
:meth:`~intents.service_connector.Connector.fulfill` on a
:class:`~intents.service_connector.Connector` instance. The result will be a
dictionary that you can return as it is.

API
===
"""
import json
import logging
import http.server
from typing import List, Union
from dataclasses import dataclass, field

import intents
from intents import LanguageCode
from intents.model.intent import Intent, FulfillmentContext, FulfillmentResult
# from intents.language import LanguageCode, IntentResponse, IntentResponseDict

logger = logging.getLogger(__name__)

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

    Args:
        body: A dict representing the request body
        headers: An optional dict containing the request headers, if present
    """
    body: dict
    headers: dict = field(default_factory=dict)

def ensure_fulfillment_result(fulfill_return_value: Union[FulfillmentResult, Intent]) -> FulfillmentResult:
    if fulfill_return_value is None:
        return

    if isinstance(fulfill_return_value, FulfillmentResult):
        return fulfill_return_value

    from intents import Intent
    if isinstance(fulfill_return_value, Intent):
        return FulfillmentResult(trigger=fulfill_return_value)

    raise ValueError(f"Unsupported fulfillment return value: {fulfill_return_value}")

#
# Development Server
#

def run_dev_server(connector: "intents.service_connector.Connector", host: str='', port: str=8000):
    """
    Spawn a simple HTTP server to receive fulfillment requests from the outside.
    This is typically used in combination with some local tunneling solution
    such as `ngrok <https://ngrok.com/>`_

    Note that the server will only release its port after its Python process
    dies. This makes it inconvenient to run within a Python CLI, because it
    would be necessary to shut the whole interpreter down at each change. Auto
    reload is not supported yet, your best option is to make a script to
    instantiate Connector and run the server.

    .. warning::

        This server uses Python builtin :mod:`http.server` module, which as per documentation only
        implements basic security check. Also the implementation of request handling is very basic
        and not thoroughly tested. Therefore, it is recommended not to run this service in production

    Args:
        connector: A Connector to direct incoming requests to
        host: Optional custom host
        port: Optional custom port
    """
    server_address = (host, port)

    # doesn't work..
    # http.server.HTTPServer.allow_reuse_address = True

    class DevWebhookHttpHandler(http.server.BaseHTTPRequestHandler):

            def do_POST(self):
                content_len = int(self.headers.get('Content-Length'))
                post_body = self.rfile.read(content_len)
                post_body = json.loads(post_body)
                logger.info("POST BODY: %s", post_body)

                fulfillment_request = FulfillmentRequest(
                    body=post_body
                )
                result = connector.fulfill(fulfillment_request)
                result = json.dumps(result)
                # result = json.dumps({"foo": "bar"})
                
                self.send_response(http.server.HTTPStatus.OK)
                self.send_header('Content-type', 'application/json')
                self.end_headers()

                logger.info("POST RESPONSE: %s", result)
                result = bytes(result, 'utf-8')
                self.wfile.write(result)
                self.wfile.flush()

    httpd = http.server.HTTPServer(server_address, DevWebhookHttpHandler)
    print(f"Starting Intents {intents.__version__} development web server on {host}:{port}")
    print("Usage of this module is strongly discouraged in production")
    httpd.serve_forever()


# from example_agent import ExampleAgent
# from intents.connectors import DialogflowEsConnector, WebhookConfiguration
# df = DialogflowEsConnector(
#     '/home/dario/lavoro/dialogflow-agents/_tmp_agents/learning-dialogflow-5827a2d16c34.json',
#     ExampleAgent,
#     default_session='testing-session'
# )
# run_dev_server(df)
