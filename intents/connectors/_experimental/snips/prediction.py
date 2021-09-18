import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Type
from collections import defaultdict

from intents import Intent, Agent, LanguageCode, FulfillmentContext, FulfillmentResult
from intents.connectors.interface import deserialize_intent_parameters, Prediction, ServiceEntityMappings
from intents.language import intent_language
from intents.connectors._experimental.snips import prediction_format as f

logger = logging.getLogger(__name__)

@dataclass
class SnipsPrediction(Prediction):
    parse_result: f.ParseResult = field(default=None, repr=False)

class SnipsPredictionComponent:
    """
    This is the component of SnipsConnector that is responsible for handling
    prediction and trigger calls.
    """

    agent_cls: Type[Agent]
    entity_mappings: ServiceEntityMappings

    def __init__(self, agent_cls: Type[Agent], entity_mappings: ServiceEntityMappings):
        self.agent_cls = agent_cls
        self.entity_mappings = entity_mappings

    def intent_from_parse_result(self, parse_result: f.ParseResult) -> Intent:
        """
        Turn SnipsNLU output into an Intent class
        """
        intent_name = parse_result.intent.intentName
        intent_cls = self.agent_cls._intents_by_name.get(intent_name)
        if not intent_cls:
            raise ValueError(f"Snips returned intent with name '{intent_name}', but this was not found in the Agent "
                            f"definition. Make sure that the model is updated by running SnipsConnector.upload() again,"
                            f"and if the problem persists please open an issue on the Intents repository.")
        snips_parameters = _slot_list_to_param_dict(intent_cls, parse_result.slots)
        parameter_dict = deserialize_intent_parameters(snips_parameters, intent_cls, self.entity_mappings)
        return intent_cls(**parameter_dict)

    def prediction_from_parse_result(self, parse_result: f.ParseResult, lang: LanguageCode) -> SnipsPrediction:
        """
        Turn SnipsNLU output into a Prediction object
        """
        intent = self.intent_from_parse_result(parse_result)
        language_data = intent_language.intent_language_data(self.agent_cls, intent.__class__, lang)
        language_data = language_data[lang]
        fulfillment_messages, fulfillment_text = intent_language.render_responses(intent, language_data)
        return SnipsPrediction(
            intent=intent,
            confidence=parse_result.intent.probability,
            fulfillment_messages=fulfillment_messages,
            fulfillment_text=fulfillment_text,
            parse_result=parse_result
        )

    def prediction_from_intent(self, intent: Intent, lang: LanguageCode) -> SnipsPrediction:
        """
        This is used to generate prediction objects in trigger requests. Normally a
        trigger is a request to a prediction service, and the response is turned
        into a prediction. As Snips runs locally, we can just return the Intent
        object as it is received.

        Note that intent relations are not implemented yet. In the future, they must
        be solved as well.
        """
        language_data = intent_language.intent_language_data(self.agent_cls, intent.__class__, lang)
        language_data = language_data[lang]
        fulfillment_messages, fulfillment_text = intent_language.render_responses(intent, language_data)
        return SnipsPrediction(
            intent=intent,
            confidence=1.0,
            fulfillment_messages=fulfillment_messages,
            fulfillment_text=fulfillment_text,
            parse_result=None
        )

    def fulfill_local(self, prediction: SnipsPrediction, lang: LanguageCode, _stack: List[str]=None) -> SnipsPrediction:
        """
        Simulate the fulfillment flow in a local procedure. This method is called
        internally by :meth:`~SnipsConnector.predict` and
        :meth:`~SnipsConnector.trigger` to solve fulfillments before returning
        the Prediction to User.

        Fulfillments are solved **recursively**, but at the moment loops are
        not allowed: intent A can trigger intent B in fulfillment, but cannot
        trigger itself. Intent B can trigger every other intent but A and B, and
        so on.

        Args:
            prediction: A prediction object, as it is built before solving
                fulfillment
            lang: Language code of the prediction
            _stack: This is used internally to prevent loops in recursion
        Returns:
            The triggered intent that is returned by predicted
            :meth:`Intent.fulfill`. If :meth:`fulfill` is not defined, or if it
            returns `None`, return the input `prediction` object
        """
        if not _stack:
            _stack = []
    
        if not prediction.intent:
            logger.warning("Prediction contains no intent: %s", prediction)
            return prediction

        if prediction.intent.name in _stack:
            raise RecursionError("Circular fulfillment calls detected: intent '%s' is being "
                                 "fulfilled twice. Stack: %s. Make sure intents aren't fulfilled "
                                 "recursively. If this is intended, open a feature request issue "
                                 "on the Intents repository", prediction.intent.name, _stack)

        _stack.append(prediction.intent.name)

        context = FulfillmentContext(
            confidence=prediction.confidence,
            fulfillment_text=prediction.fulfillment_text,
            fulfillment_messages=prediction.fulfillment_messages,
            language=lang
        )
        fulfillment_result = FulfillmentResult.ensure(prediction.intent.fulfill(context))
        if fulfillment_result:
            if fulfillment_result.trigger:
                triggered = self.prediction_from_intent(fulfillment_result.trigger, lang)
                return self.fulfill_local(triggered, lang, _stack=_stack)
            else:
                logger.warning("Intent returned a fulfillment result without trigger. Trigger "
                               "is the only supported response in SnipsConnector. Other elements "
                               "will be ignored.")
        return prediction

def _slot_list_to_param_dict(
    intent_cls: Type[Intent],
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
