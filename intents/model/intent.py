import re
import logging
import dataclasses
from dataclasses import dataclass, is_dataclass
from typing import List, Dict, Any, _GenericAlias

from intents.model import context, event, entity

logger = logging.getLogger(__name__)

#
# Fulfillment Messages
#

class FulfillmentMessage:
    """
    This is a base class for Intent Fulfillment Messages
    """

class TextFulfillmentMessage(str, FulfillmentMessage):
    """
    This is a simple text fulfillment message.
    """

#
# Intent
#

@dataclass
class IntentParameterMetadata:
    name: str
    entity_cls: entity._EntityMetaclass
    is_list: bool
    required: bool
    default: Any

class _IntentMetaclass(type):

    name: str = None
    input_contexts: List[context._ContextMetaclass] = None
    output_contexts: List[context.Context] = None
    events: List[event.Event] = None # TODO: at some point this may contain strings

    def __new__(cls, name, bases, dct):
        result_cls = super().__new__(cls, name, bases, dct)

        # Do not process Intent base class
        if name == 'Intent':
            assert not bases
            return result_cls

        if not result_cls.name:
            result_cls.name = _intent_name_from_class(result_cls)
        else:
            is_valid, reason = _is_valid_intent_name(result_cls.name)
            if not is_valid:
                raise ValueError(f"Invalid intent name '{result_cls.name}': {reason}")

        if not result_cls.input_contexts:
            result_cls.input_contexts = []
        if not result_cls.output_contexts:
            result_cls.output_contexts = []

        # TODO: check that custom parameters don't overlap Intent fields
        # TODO: check language data
        # language.intent_language_data(cls, result) # Checks that language data is existing and consistent

        events = [_system_event(result_cls.name)]
        for event_cls in result_cls.__dict__.get('events', []):
            events.append(event_cls)
        result_cls.events = events

        if not is_dataclass(result_cls):
            result_cls = dataclass(result_cls)

        # Check parameters
        result_cls.parameter_schema()

        return result_cls

class Intent(metaclass=_IntentMetaclass):
    """
    Represents a predicted intent. This is also used as a base class for the
    intent classes that model a Dialogflow Agent in Python code.

    TODO: check parameter names: no underscore, no reserved names, max length
    """

    name: str = None
    input_contexts: List[context._ContextMetaclass] = None
    output_contexts: List[context.Context] = None
    events: List[event.Event] = None # TODO: at some point this may contain strings

    # A :class:`ServiceConnector` provides this
    prediction: 'intents.Prediction'

    @property
    def confidence(self) -> float:
        return self.prediction.confidence

    @property
    def contexts(self) -> list:
        return self.prediction.contexts

    @property
    def fulfillment_text(self) -> str:
        return self.prediction.fulfillment_text

    def fulfillment_messages(self) -> List[FulfillmentMessage]:
        return self.prediction.fulfillment_messages

    # def fulfillment_messages(self, platform: FulfillmentMessagePlatform=None) -> List[FulfillmentMessage]:
    #     if not platform:
    #         platform = FulfillmentMessagePlatform.PLATFORM_UNSPECIFIED

    #     result_per_platform = defaultdict(list)
    #     for m in self._prediction.fulfillment_messages:
    #         m_platform = FulfillmentMessagePlatform(m.platform)
    #         result_per_platform[m_platform].append(build_response_message(m))

    #     return result_per_platform[platform]

    @classmethod
    def parameter_schema(cls) -> Dict[str, IntentParameterMetadata]:
        """
        Return a dict representing the Intent parameter definition. A key is a
        parameter name, a value is a :class:`IntentParameterMetadata` object.

        TODO: consider computing this in metaclass to cache value and check types
        """
        result = {}
        for param_field in cls.__dict__['__dataclass_fields__'].values():
            # List[...]
            if isinstance(param_field.type, _GenericAlias):
                if param_field.type.__dict__.get('_name') != 'List':
                    raise ValueError(f"Invalid typing '{param_field.type}' for parameter '{param_field.name}'. Only 'List' is supported.")

                if len(param_field.type.__dict__.get('__args__')) != 1:
                    raise ValueError(f"Invalid List modifier '{param_field.type}' for parameter '{param_field.name}'. Must define exactly one inner type (e.g. 'List[Sys.Any]')")
                
                # From here on, check the inner type (e.g. List[Sys.any] -> Sys.Any)
                entity_cls = param_field.type.__dict__.get('__args__')[0]
                is_list = True
            else:
                entity_cls = param_field.type
                is_list = False

            required = True
            default = None
            if not isinstance(param_field.default, dataclasses._MISSING_TYPE):
                required = False
                default = param_field.default
            if not isinstance(param_field.default_factory, dataclasses._MISSING_TYPE):
                required = False
                default = param_field.default_factory()

            if not required and is_list and not isinstance(default, list):
                raise ValueError(f"List parameter has non-list default value in intent {cls}: {param_field}")

            result[param_field.name] = IntentParameterMetadata(
                name=param_field.name,
                entity_cls=entity_cls,
                is_list=is_list,
                required=required,
                default=default
            )

        return result

    @classmethod
    def from_prediction(cls, prediction: 'intents.Prediction') -> 'Intent':
        """
        Build an :class:`Intent` class from a :class:`Prediction`. In practice:

        #. Match parameters givent the Intent schema
        #. Instantiate the Intent
        #. Set the `prediction` field on the instantiated Intent.
        """
        try:
            parameters = prediction.parameters(cls.parameter_schema())
        except ValueError as exc:
            raise ValueError(f"Failed to match parameters for Intent class '{cls}'. Prediction: {prediction}") from exc

        result = cls(**parameters)
        result.prediction = prediction
        return result

def _is_valid_intent_name(candidate_name):
    if re.search(r'[^a-zA-Z_\.]', candidate_name):
        return False, "must only contain letters, underscore or dot"

    if candidate_name.startswith('.') or candidate_name.startswith('_'):
        return False, "must start with a letter"

    if "__" in candidate_name:
        return False, "must not contain __"

    return True, None

def _intent_name_from_class(intent_cls: _IntentMetaclass) -> str:
    full_name = f"{intent_cls.__module__}.{intent_cls.__name__}"
    if "__" in full_name:
        logger.warning("Intent class '%s' contains repeated '_'. This is reserved: repeated underscores will be reduced to one, this may cause unexpected behavior.")
    full_name = re.sub(r"_+", "_", full_name)
    return ".".join(full_name.split(".")[-2:])

def _system_event(intent_name: str) -> str:
    """
    Generate the default event name that we associate with every intent.

    >>> _event_name('test.intent_name')
    'E_TEST_INTENT_NAME'

    TODO: This is only used in Dialogflow -> Deprecate and move to DialogflowConnector
    """
    event_name = "E_" + intent_name.upper().replace('.', '_')
    return event.SystemEvent(event_name)

# @dataclass
# class MyIntent(Intent):
#     a_param: str

# i = MyIntent(42)
