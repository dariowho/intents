"""
Connectors allow *Intents* Agent definitions to operate with real cloud services
such as Dialogflow, Lex or Azure Bot Services. Currently, only one stable connector is
provided with this library, and this is for Dialogflow ES:
:mod:`intents.connectors.dialogflow_es.connector`.

.. note::

    Details about the Connector interface are only useful if you intend to develop your own Service Connector (please consider raising a pull request if this is the case). If you just need to use the included Dialogflow Connector you can jump to its documentation page right away: :mod:`intents.connectors.dialogflow_es.connector`

Connectors are used to operate with the cloud version of the Agent, and
specifically to:

* Export an :class:`intents.Agent` in a format that is natively readable by the
  Service
* Predict User messages and trigger intents on the Cloud Agent
* Handle intent fulfillment requests by Service
"""
from intents.connectors.interface.connector import Connector
from intents.connectors.interface.entity_mappings import EntityMapping, \
    StringEntityMapping, PatchedEntityMapping, ServiceEntityMappings, deserialize_intent_parameters
from intents.connectors.interface.fulfillment import FulfillmentRequest, WebhookConfiguration
from intents.connectors.interface.prediction import Prediction
