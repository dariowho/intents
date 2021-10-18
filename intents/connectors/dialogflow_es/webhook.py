"""
Here we manage Dialogflow webhook results
"""
import logging

from intents import FulfillmentResult, FulfillmentContext, LanguageCode
from intents.helpers.data_classes import to_dict
from intents.connectors.dialogflow_es.names import event_name
from intents.connectors.dialogflow_es.entities import MAPPINGS
from intents.connectors.dialogflow_es import webhook_format as wf
from intents.connectors.interface import serialize_intent_parameters

logger = logging.getLogger(__name__)

def fulfillment_result_to_response(fulfillment_result: FulfillmentResult, context: FulfillmentContext) -> dict:
    if fulfillment_result.trigger:
        intent = fulfillment_result.trigger
        followup_event = wf.WebhookResponseFollowupEvent(
            name=event_name(intent),
            languageCode=LanguageCode.ensure(context.language).value,
            parameters=serialize_intent_parameters(intent, MAPPINGS)
        )
        return to_dict(wf.WebhookResponse(
            followupEventInput=followup_event
        ))
    else:
        logger.warning("No trigger in fulfillment result. Triggers are the only fulfillment "
                       "response available in DialogflowEsConnector at the moment. Will send "
                       "empty response.")
    return {}
