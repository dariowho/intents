"""
...
"""
import abc
from dataclasses import dataclass
from typing import DefaultDict, Dict, List

import intents as it
from intents.connectors.interface.connector import Connector

@dataclass
class RecordedFulfillmentCall:
    intent: it.Intent
    context: it.FulfillmentContext
    result: it.FulfillmentResult

class TestableConnector(Connector):
    """
    A Connector that implements this interface will record every fulfillment
    call that is received while :var:`is_recording_enabled` is `True`.
    :var:`recorded_fulfillment_calls` will contain the list of fulfillment calls
    per each conversation section.

    This is used at test time to make assertions on fulfillments, that would be
    otherwise hidden in the webhook mechanics.
    """
    is_recording_enabled: bool = False
    recorded_fulfillment_calls: DefaultDict[str, List[RecordedFulfillmentCall]]
