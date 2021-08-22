"""
Here we manage webhook results
"""
import logging

from intents import FulfillmentResult, FulfillmentContext
from intents.language_codes import ensure_language_code
from intents.helpers.data_classes import to_dict
from intents.connectors.dialogflow_es.names import event_name
from intents.connectors.dialogflow_es import webhook_format as wf

logger = logging.getLogger(__name__)

def fulfillment_result_to_response(fulfillment_result: FulfillmentResult, context: FulfillmentContext) -> dict:
    if fulfillment_result.trigger:
        intent = fulfillment_result.trigger
        followup_event = wf.WebhookResponseFollowupEvent(
            name=event_name(intent),
            languageCode=ensure_language_code(context.language).value,
            parameters=intent.parameter_dict()
        )
        return to_dict(wf.WebhookResponse(
            followupEventInput=followup_event
        ))
    else:
        logger.warning("No trigger in fulfillment result. Triggers are the only fulfillment "
                       "response available in DialogflowEsConnector at the moment. Will send "
                       "empty response.")
    return {}
