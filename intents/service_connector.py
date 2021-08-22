"""
This module is **deprecated**. Use :mod:`intents.connectors.interface` instead
"""
import warnings

warnings.warn("intents.service_connector is DEPRECATED and will be removed in v0.4.0. "
              "Use intents.connectors.interface instead", DeprecationWarning)

from intents.connectors.interface.connector import Connector
from intents.connectors.interface.entity_mappings import EntityMapping, StringEntityMapping, PatchedEntityMapping, ServiceEntityMappings, deserialize_intent_parameters
from intents.connectors.interface.fulfillment import FulfillmentRequest
from intents.connectors.interface.prediction import Prediction
