import logging
from dataclasses import dataclass
from typing import Dict, List, Any
from collections import defaultdict

from intents import Intent, LanguageCode
from intents.model.intent import _IntentMetaclass
from intents.service_connector import deserialize_intent_parameters, Prediction
from intents.language import intent_language, IntentLanguageData, IntentResponse, IntentResponseGroup
from intents.connectors._experimental.snips import SnipsConnector
from intents.connectors._experimental.snips import prediction_format as f

logger = logging.getLogger(__name__)

@dataclass
class SnipsPrediction(Prediction):
    parse_result: f.ParseResult = None

def intent_from_parse_result(connector: SnipsConnector, parse_result: f.ParseResult) -> Intent:
    intent_cls = connector.agent_cls._intents_by_name.get(parse_result.intent.intentName)
    if not intent_cls:
        raise ValueError(f"Snips returned intent with name '{intent_cls}', but this was not found in the Agent "
                         f"definition. Make sure that the model is updated by running SnipsConnector.fit() again,"
                         f"and if the problem persists please open an issue on the Intents repository.")
    snips_parameters = _slot_list_to_param_dict(intent_cls, parse_result.slots)
    parameter_dict = deserialize_intent_parameters(snips_parameters, intent_cls, connector.entity_mappings)
    return intent_cls(**parameter_dict)

def _slot_list_to_param_dict(
    intent_cls: _IntentMetaclass,
    result_slots: List[f.ParseResultSlot]
) -> Dict[str, Any]:
    """
    Snips doesn't differentiate between list and non-list parameters. If an
    entity can be tagged multiple times, result slots will contain more than one
    match for that entity, even if the slot is not meant to be a list. So here we:

    * Collect matches per slot as lists
    * Pick first element for non-list parameters

    The resulting parameter dict can be fed to
    :func:`deserialize_intent_parameters` without the risk of raising exceptions
    """
    result_lists = defaultdict(list)
    for slot in result_slots:
        result_lists[slot.slotName].append(slot.value)

    result = {}
    schema = intent_cls.parameter_schema
    for slot_name, slot_values in result_lists.items():
        if slot_name not in schema:
            raise KeyError(f"Slot {slot_name} not found in intent {intent_cls} with schema: "
                           f"{schema}. Make sure your trained model is up to date with the "
                           "latest Agent definition. If it is, please file a bug in the Intents "
                           "repository")
        if schema[slot_name].is_list:
            result[slot_name] = slot_values
        else:
            if len(slot_values) > 1:
                logger.warning("Prediction returned more than one value for slot %s: %s. "
                               "Only the first value will be considered.")
            result[slot_name] = slot_values[0]
    return result

def _render_responses(intent: Intent, language_data: IntentLanguageData):
    result_messages: Dict[IntentResponseGroup, IntentResponse] = {}
    for group, response_list in language_data.responses.items():
        result_messages[group] = [r.render(intent) for r in response_list]
    rendered_plaintext = [r.random() for r in result_messages.get(IntentResponseGroup.DEFAULT, [])]
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
