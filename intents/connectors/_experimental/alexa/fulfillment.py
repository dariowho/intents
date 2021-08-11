"""
Here we implement fulfillment handling. This module is responsible for parsing
requests from Alexa, build Intent objects, solve relations and run fulfillment
procedures.
"""
import logging
from dataclasses import dataclass, replace, field
from typing import Dict, List, Any, Tuple
from collections import defaultdict

from intents import Intent, LanguageCode
from intents.types import IntentType, AgentType
from intents.model.fulfillment import FulfillmentContext, ensure_fulfillment_result
from intents.service_connector import deserialize_intent_parameters, Prediction, ServiceEntityMappings
from intents.language import intent_language, IntentLanguageData, IntentResponse, IntentResponseGroup, IntentResponseDict
from intents.connectors._experimental.alexa import fulfillment_schemas as fs
from intents.connectors._experimental.alexa import names, slot_types

logger = logging.getLogger(__name__)

@dataclass
class AlexaPrediction(Prediction):
    fulfillment_request: fs.FulfillmentBody = field(default=None, repr=False)

class AlexaFulfillmentComponent:
    """
    This is the component of SnipsConnector that is responsible for handling
    fulfillment requests and... TODO: complete.
    """

    agent_cls: AgentType
    names_component: names.AlexaNamesComponent

    def __init__(self, agent_cls: AgentType, names_component: names.AlexaNamesComponent):
        self.agent_cls = agent_cls
        self.names_component = names_component

    def intent_from_fulfillment(self, fulfillment_body: fs.FulfillmentBody):
        alexa_intent_name = fulfillment_body.request.intent.name
        intent_name = self.names_component.alexa_to_intent_name(alexa_intent_name)
        intent_cls = self.agent_cls._intents_by_name.get(intent_name)
        if not intent_cls:
            raise ValueError(f"Alexa returned intent with name '{alexa_intent_name}', but this was not found in the Agent "
                             f"definition. Make sure that the cloud agent is up to date with model,"
                             f"and if the problem persists please open an issue on the Intents repository.")
        
        request_slots = list(fulfillment_body.request.intent.slots.values())
        alexa_parameters = self._slots_to_param_dict(intent_cls, request_slots)
        parameter_dict = deserialize_intent_parameters(alexa_parameters, intent_cls, slot_types.ENTITY_MAPPINGS)
        return intent_cls(**parameter_dict)

    def prediction_from_fulfillment(self, fulfillment_body: fs.FulfillmentBody):
        raise NotImplementedError()

    def _slots_to_param_dict(self, intent_cls: IntentType, request_slots: List[fs.FulfillmentIntentRequestIntentSlot]) -> Dict[str, Any]:
        parameter_schema = intent_cls.parameter_schema

        # TODO: map custom slot values with language.alexa_entry_id_to_value

        result = {}
        for slot in request_slots:
            slot: fs.FulfillmentIntentRequestIntentSlot

            if slot.name not in parameter_schema:
                raise ValueError(f"Alexa returned slot name '{slot.name}', but this is not defined in "
                                 f"Intent '{intent_cls}' with parameter schema: {parameter_schema}. "
                                 "Make sure that your cloud agent is up to date with your code, and "
                                 "if the problem persist please file an issue on the Intents repository/")

            if slot.slotValue.type == fs.SlotType.SIMPLE:
                value = slot.slotValue.value
                if parameter_schema[slot.name].is_list:
                    logger.warning("Parameter '%s.%s' is defined as list, but Alexa returned a single "
                                   "value ('%s'). Will be converted to list", intent_cls.name, slot.name,
                                   value)
                    value = [value]
            else:
                value = []
                for v in slot.slotValue.values:
                    if v.type != fs.SlotType.SIMPLE:
                        logger.warning("Slot value for parameter '%s.%s' contains nested lists. This is "
                                       "not supported, nested lists will be skipped.")
                        continue
                    value.append(v.value)

                if not parameter_schema[slot.name].is_list:
                    logger.warning("Alexa returned a list value for parameter '%s.%s' ('%s'), but "
                                   "parameter is not defined as list. Only the first element will be "
                                   "returned", intent_cls.name, slot.name, value)
                    value = value[0]

            result[slot.name] = value

        return result
