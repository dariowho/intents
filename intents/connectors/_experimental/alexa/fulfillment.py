"""
Here we implement fulfillment handling. This module is responsible for parsing
requests from Alexa, build Intent objects, solve relations and run fulfillment
procedures.
"""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any, Type

from intents import Intent, Agent, LanguageCode, FulfillmentContext, FulfillmentResult
from intents.connectors.interface import deserialize_intent_parameters, Prediction
from intents.language import intent_language
from intents.connectors._experimental.alexa import fulfillment_schemas as fs
from intents.connectors._experimental.alexa import names, slot_types, language

logger = logging.getLogger(__name__)

@dataclass
class AlexaPrediction(Prediction):
    fulfillment_request: fs.FulfillmentBody = field(default=None, repr=False)

class AlexaFulfillmentComponent:
    """
    This is the component of AlexaConnector that is responsible for handling
    fulfillment requests and... TODO: complete.
    """

    agent_cls: Type[Agent]
    names_component: names.AlexaNamesComponent
    language_component: language.AlexaLanguageComponent

    def __init__(
        self,
        agent_cls: Type[Agent],
        names_component: names.AlexaNamesComponent,
        language_component: language.AlexaLanguageComponent
    ):
        self.agent_cls = agent_cls
        self.names_component = names_component
        self.language_component = language_component

    def handle_fulfillment(self, request_body: fs.FulfillmentBody) -> fs.FulfillmentResponseBody:
        if request_body.request.type == fs.RequestType.LAUNCH:
            return _make_speech_response("Skill launched!")

        if request_body.request.type == fs.RequestType.SESSION_ENDED:
            return fs.FulfillmentResponseBody()

        locale = request_body.request.locale
        lang = self.language_component.alexa_locale_to_agent_language(locale)
        intent = self.intent_from_fulfillment(request_body, lang)
        result_text = self.fulfill_local(intent, lang)
        return _make_speech_response(result_text)

    def fulfill_local(
        self,
        intent: Intent,
        lang: LanguageCode,
        _stack: List[str]=None
    ) -> str:
        """
        Resolve recursive fulfillment triggers locally, 
        """
        if not _stack:
            _stack = []

        if intent.name in _stack:
            raise RecursionError("Circular fulfillment calls detected: intent '%s' is being "
                                 "fulfilled twice. Stack: %s. Make sure intents aren't fulfilled "
                                 "recursively. If this is intended, open a feature request issue "
                                 "on the Intents repository", intent.name, _stack)

        _stack.append(intent.name)

        language_data = intent_language.intent_language_data(self.agent_cls, intent.__class__, lang)[lang]
        rendered_messages, rendered_plaintext = intent_language.render_responses(intent, language_data)
        context = FulfillmentContext(
            confidence=1.0,
            fulfillment_text=rendered_plaintext,
            fulfillment_messages=rendered_messages,
            language=lang
        )
        fulfillment_result = FulfillmentResult.ensure(intent.fulfill(context))

        if fulfillment_result:
            if fulfillment_result.trigger:
                return self.fulfill_local(fulfillment_result.trigger, lang, _stack=_stack)
            else:
                logger.warning("Intent returned a fulfillment result without trigger. Trigger "
                               "is the only supported response in SnipsConnector. Other elements "
                               "will be ignored.")

        return rendered_plaintext

    def intent_from_fulfillment(self, request_body: fs.FulfillmentBody, lang: LanguageCode) -> Intent:
        alexa_intent_name = request_body.request.intent.name
        intent_name = self.names_component.alexa_to_intent_name(alexa_intent_name)
        intent_cls = self.agent_cls._intents_by_name.get(intent_name)
        if not intent_cls:
            raise ValueError(f"Alexa returned intent with name '{alexa_intent_name}', but this was not found in the Agent "
                             f"definition. Make sure that the cloud agent is up to date with model,"
                             f"and if the problem persists please open an issue on the Intents repository.")
        
        request_slots = list(request_body.request.intent.slots.values())
        alexa_parameters = self._slots_to_param_dict(intent_cls, request_slots, lang)
        parameter_dict = deserialize_intent_parameters(alexa_parameters, intent_cls, slot_types.ENTITY_MAPPINGS)
        return intent_cls(**parameter_dict)

    def fulfillment_result_to_response(
        self,
        fulfillment_result: FulfillmentResult,
        context: FulfillmentContext    
    ) -> fs.FulfillmentResponseBody:

        # No fulfillment -> return intent responses
        if not fulfillment_result:
            print("no result: Returning messages")
            result = fs.FulfillmentResponseBody(
                response=fs.FulfillmentResponse(
                    outputSpeech=fs.FulfillmentResponseOutputSpeech(
                        type=fs.OutputSpeechType.PlainText,
                        text=context.fulfillment_text
                    )
                )
            )
            print(result)
            return result

        # TODO: doesn't work
        # Fulfillment result -> trigger
        fulfillment_result = FulfillmentResult.ensure(fulfillment_result)
        if fulfillment_result.trigger:
            intent: Intent = fulfillment_result.trigger
            return fs.FulfillmentResponseBody(
                # TODO: set attributes to track context
                response=fs.FulfillmentResponse(
                    directives=fs.FulfillmentResponseDialogDelegateDirective(
                        updatedIntent=fs.FulfillmentResponseDialogDelegateUpdatedIntent(
                            name=self.names_component.intent_to_alexa(intent),
                            confirmationStatus=fs.IntentConfirmationStatus.NONE,
                            slots=self._slots_from_intent(intent)
                        )
                    )
                )
            )
        logger.warning("No trigger in fulfillment result: ignoring")

    def prediction_from_fulfillment(self, request_body: fs.FulfillmentBody):
        raise NotImplementedError()

    def _slots_to_param_dict(
        self,
        intent_cls: Type[Intent],
        request_slots: List[fs.IntentSlot],
        lang: LanguageCode
    ) -> Dict[str, Any]:
        parameter_schema = intent_cls.parameter_schema

        # TODO: map custom slot values with language.alexa_entry_id_to_value

        result = {}
        for slot in request_slots:
            slot: fs.IntentSlot

            # Slot not matched in utterance
            if not slot.slotValue:
                continue

            # System slots, like "__Conjunction"
            if slot.name.startswith("__"):
                continue

            if slot.name not in parameter_schema:
                raise ValueError(f"Alexa returned slot name '{slot.name}', but this is not defined in "
                                 f"Intent '{intent_cls}' with parameter schema: {parameter_schema}. "
                                 "Make sure that your cloud agent is up to date with your code, and "
                                 "if the problem persist please file an issue on the Intents repository/")

            if slot.slotValue.type == fs.SlotType.SIMPLE:
                value = self._get_simple_slot_value(slot.slotValue, lang)
                
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
                    value.append(self._get_simple_slot_value(v, lang))

                if not parameter_schema[slot.name].is_list:
                    logger.warning("Alexa returned a list value for parameter '%s.%s' ('%s'), but "
                                   "parameter is not defined as list. Only the first element will be "
                                   "returned", intent_cls.name, slot.name, value)
                    value = value[0]

            result[slot.name] = value

        return result

    def _get_simple_slot_value(
        self,
        slot_value: fs.IntentSlotValue,
        lang: LanguageCode
    ) -> Any:
        """
            # Amazon: meh...
            value = slot.value
            
            # Amazon: perfect
            value = slot.slotValue.resolutions.resolutionsPerAuthority[0].values[0].value.name
        """
        # Some entities have resolutions, and canonical value is hidden there
        if slot_value.resolutions:
            authority_resolution = slot_value.resolutions.resolutionsPerAuthority[0]
            
            # System entities are returned as they are
            if authority_resolution.authority == "AlexaEntities":
                return authority_resolution.values[0].value.name
            
            # Custom entities are looked up by id
            entry_id = authority_resolution.values[0].value.id
            return self.language_component.alexa_entry_id_to_value(entry_id, lang)

        # Some entities don't, and canonical value is at top level
        return slot_value.value

    def _slots_from_intent(self, intent: Intent) -> Dict[str, fs.IntentSlot]:
        result = {}
        parameter_schema = intent.parameter_schema
        for param_name, param_value in intent.parameter_dict().items():
            entity_cls = parameter_schema[param_name].entity_cls
            mapping = slot_types.ENTITY_MAPPINGS.lookup(entity_cls)
            result[param_name] = fs.IntentSlot(
                confirmationStatus=fs.IntentConfirmationStatus.NONE,
                name=param_name,
                value=mapping.to_service(param_value)
            )
        return result

def _make_speech_response(text: str) -> fs.FulfillmentResponseBody:
    return fs.FulfillmentResponseBody(
        response=fs.FulfillmentResponse(
            outputSpeech=fs.FulfillmentResponseOutputSpeech(
                type=fs.OutputSpeechType.PlainText,
                text=text
            ),
            shouldEndSession=False
        )
    )