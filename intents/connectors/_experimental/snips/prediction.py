from dataclasses import dataclass
from typing import Dict

from intents import Intent, LanguageCode
from intents.service_connector import deserialize_intent_parameters, Prediction
from intents.language import intent_language, IntentLanguageData, IntentResponse, IntentResponseGroup
from intents.connectors._experimental.snips import SnipsConnector
from intents.connectors._experimental.snips import prediction_format as f

@dataclass
class SnipsPrediction(Prediction):
    parse_result: f.ParseResult = None

def intent_from_parse_result(connector: SnipsConnector, parse_result: f.ParseResult) -> Intent:
    intent_cls = connector.agent_cls._intents_by_name.get(parse_result.intent.intentName)
    if not intent_cls:
        raise ValueError(f"Snips returned intent with name '{intent_cls}', but this was not found in the Agent "
                         f"definition. Make sure that the model is updated by running SnipsConnector.fit() again,"
                         f"and if the problem persists please open an issue on the Intents repository.")
    snips_parameters = {slot.slotName: slot.value["value"] for slot in parse_result.slots}
    parameter_dict = deserialize_intent_parameters(snips_parameters, intent_cls, connector.entity_mappings)
    return intent_cls(**parameter_dict)

def _render_responses(intent: Intent, language_data: IntentLanguageData):
    result_messages: Dict[IntentResponseGroup, IntentResponse] = {}
    for group, response_list in language_data.responses.items():
        result_messages[group] = [r.render(intent) for r in response_list]
    rendered_plaintext = [r.choose() for r in result_messages.get(IntentResponseGroup.DEFAULT, [])]
    result_plaintext = " ".join(rendered_plaintext)
    return result_messages, result_plaintext

def prediction_from_parse_result(connector: SnipsConnector, parse_result: f.ParseResult, lang: LanguageCode):
    intent = intent_from_parse_result(connector, parse_result)
    language_data = intent_language.intent_language_data(connector.agent_cls, intent.__class__, lang)
    language_data = language_data[lang]
    fulfillment_messages, fulfillment_text = _render_responses(intent, language_data)
    return SnipsPrediction(
        intent=intent,
        confidence=parse_result.intent.probability,
        fulfillment_message_dict=fulfillment_messages,
        fulfillment_text=fulfillment_text,
        parse_result=parse_result
    )
