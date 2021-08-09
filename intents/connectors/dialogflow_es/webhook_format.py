"""
Here we model Dialogflow payloads that are involved in webhook fulfillment calls.
"""
from typing import List
from dataclasses import dataclass

from intents.helpers.data_classes import OmitNone
from intents.connectors.dialogflow_es import prediction_format as pf

#
# Request
#

# Webhook requests are very similar to prediction requests. Models are the same
# ones defined in :mod:`prediction_format.py`

#
# Response
#

@dataclass
class WebhookResponseFollowupEvent:
    name: str
    languageCode: str
    parameters: dict

@dataclass
class WebhookResponse:
    followupEventInput: WebhookResponseFollowupEvent
    fulfillmentMessages: List[pf.QueryResultMessage] = OmitNone()
    # payload: TODO
    # outputContexts: TODO
    # sessionEntityTypes: TODO
