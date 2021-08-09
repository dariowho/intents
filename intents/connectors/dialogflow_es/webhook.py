"""
Here we manage webhook results
"""
from intents.language_codes import ensure_language_code
from intents.helpers.data_classes import to_dict
from intents.model.fulfillment import FulfillmentResult, FulfillmentContext
from intents.connectors.dialogflow_es.names import event_name
from intents.connectors.dialogflow_es import webhook_format as wf

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
    return {}
