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

    from intents import Intent, FulfillmentContext

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
build the appropriate :class:`~intents.model.intent.Intent` instance, call
:meth:`~intents.model.intent.Intent.fulfill` on it, and return its response in
the correct Service format. A **development server** is included, to
conveniently receive REST webhook calls and route them to a Connector; see
:func:`run_dev_server` for details.

We notice that :meth:`~intents.model.intent.Intent.fulfill` returns
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
   :meth:`~intents.connectors.interface.Connector.predict`, or through some native
   service integration (Dialogflow natively supports Telegram, Slack, and so on).
#. Service predicts an Intent and its parameter values
#. Service sends a fulfillment request to its configured endpoint (that's us)
#. *Intents* fulfillment framework receives the reuest and builds a
   :class:`FulfillmentRequest` object.
#. Fulfillment framework passes the :class:`FulfillmentRequest` object to the
   :meth:`~intents.connectors.interface.Connector.fulfill` method of
   :class:`~intents.connectors.interface.Connector`.
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
:func:`run_dev_server`). This is the only function exposed by
:mod:`intents.fulfillment`.

For production you must write your own; this is supposed to be fairly simple:
only thing your endpoint should do is to build a :class:`FulfillmentRequest`
object out of request data, and call
:meth:`~intents.connectors.interface.Connector.fulfill` on a
:class:`~intents.connectors.interface.Connector` instance. The result will be a
dictionary that you can return as it is.

"""
import json
import logging
import http.server

import intents
from intents.helpers.logging import jsondict
from intents.connectors.interface import Connector, FulfillmentRequest

logger = logging.getLogger(__name__)

def run_dev_server(connector: Connector, host: str='', port: str=8000):
    """
    Spawn a simple HTTP server to receive fulfillment requests from the outside.
    This is typically used in combination with some local tunneling solution
    such as `ngrok <https://ngrok.com/>`_

    .. code-block:: python

        from intents.fulfillment import run_dev_server
        from intents.connectors import DialogflowEsConnector, WebhookConfiguration
        from example_agent import ExampleAgent

        webhook = WebhookConfiguration('https://<MY-ADDRESS>.ngrok.io', {"X-Foo": "bar"})
        df = DialogflowEsConnector(..., ExampleAgent, webhook_configuration=webhook)
        df.upload()  # Will set webhook address in Dialogflow
        run_dev_server(df)

    After running the example above, prediction calls (either from
    :meth:`df.predict` or from the Dialogflow UI) will result in Dialogflow
    calling the webhook endpoint for fulfillment. You can try it with the
    intents defined in :mod:`example_agent.calculator`.

    Note that the server will only release its port after its Python process
    dies. This makes it inconvenient to run within a Python CLI, because it
    would be necessary to shut the whole interpreter down at each change. Auto
    reload is not supported yet, your best option is to make a script to
    instantiate Connector and run the server.

    .. warning::

        This server uses Python builtin :mod:`http.server` module, which as per documentation only
        implements basic security check. Also the implementation of request handling is very basic
        and not thoroughly tested. Therefore, it is recommended not to run this service in
        production

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
            logger.info("POST REQUEST BODY: %s", jsondict(post_body))

            fulfillment_request = FulfillmentRequest(
                body=post_body
            )
            result = connector.fulfill(fulfillment_request)
            logger.info("POST RESPONSE: %s", jsondict(result))
            result = json.dumps(result)
            
            self.send_response(http.server.HTTPStatus.OK)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

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
