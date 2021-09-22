"""
Intent Parameters are :class:`~intents.model.intent.Intent` class members. There
are two kinds of parameter in *Intents*:

* **NLU Parameters** are Entity types (or list of entities). They can be tagged
  in User utterance and extracted at prediction time. They are modelled by
  :class:`NluIntentParameter`.
* **SessionParameters** are values that are injected in the Conversation context
  via software, either when triggering an intent, or at
  :mod:`~intent.model.fulfillment` time. Session parameters can contain complex
  structured data, but cannot be tagged in user utterances; therefore an intent with
  Session parameters will never be predicted. Session Parameters are modelled in
  :class:`SessionIntentParameter`.
"""
import json
import logging
import dataclasses
from dataclasses import dataclass
from typing import Dict, Tuple, Any, Type, T, _GenericAlias

from dacite import from_dict

# pylint: disable=unused-import # needed for docs
import intents
from intents import LanguageCode
from intents.model import entity, names
from intents.helpers.data_classes import is_dataclass_strict, to_dict

logger = logging.getLogger(__name__)

@dataclass
class IntentParameter:
    """
    Model metadata of a single Intent parameter. `NluIntentParameter`
    objects are built internally by :attr:`Intent.parameter_schema` based on the
    Intent dataclass fields.

    >>> OrderPizzaIntent.parameter_schema
    {
        'pizza_type': NluIntentParameter(name='pizza_type', entity_cls=<...PizzaType'>, is_list=False, required=True, default=None),
        'amount': NluIntentParameter(name='amount', entity_cls=<...Sys.Integer'>, is_list=False, required=False, default=1)
    }

    This is a **base class** for two different kinds of intent parameters:

    * :class:`NluParameter` - Those that are tagged in User utterances
    * :class:`SessionParameter` - Those that are injected in session by triggers
      and fulfillments

    Args:
        name: Parameter name
        entity_cls: Parameter type
        is_list: Parameter will match multiple values in the User utterance
        required: If True, user will be prompted for parameter value when that
            can't be tagged in his utterance
        default: If set, this value will be used when parameter value can't be
            tagged in the User's utterance
    """
    name: str
    required: bool
    default: Any

@dataclass
class NluIntentParameter(IntentParameter):
    """
    These are :class:`IntentParameter`\ s that are tagged in User utterances
    (e.g. a `pizza_type` parameter can be tagged in the message of a user that
    is ordering pizza).

    Every member of an :class:`Intent` dataclass that is annotated with an
    Entity type will be recognized as a NLU Parameter.

    Args:
        name: Parameter name
        entity_cls: Parameter type
        is_list: Parameter will match multiple values in the User utterance
        required: If True, user will be prompted for parameter value when that
            can't be tagged in his utterance
        default: If set, this value will be used when parameter value can't be
            tagged in the User's utterance
    """
    is_list: bool
    entity_cls: entity.EntityType

    @staticmethod
    def from_dataclass_field(param_field: dataclasses.Field) -> "NluIntentParameter":
        if isinstance(param_field.type, _GenericAlias):
            if param_field.type.__dict__.get('_name') != 'List':
                raise ValueError(f"Invalid typing '{param_field.type}' for NLU Parameter '{param_field.name}'. Only 'List' is supported.")

            if len(param_field.type.__dict__.get('__args__')) != 1:
                raise ValueError(f"Invalid List modifier '{param_field.type}' for NLU Parameter '{param_field.name}'. Must define exactly one inner type (e.g. 'List[Sys.Integer]')")
            
            # From here on, check the inner type (e.g. List[Sys.Integer] -> Sys.Integer)
            entity_cls = param_field.type.__dict__.get('__args__')[0]
            is_list = True
        else:
            entity_cls = param_field.type
            is_list = False

        if not issubclass(entity_cls, entity.EntityMixin):
            raise ValueError(f"NLU Parameter '{param_field.name}' is of type '{entity_cls}', which is not an Entity.")

        required, default = _is_required(param_field)

        if not required and is_list and not isinstance(default, list):
            raise ValueError(f"List NLU Parameter {param_field.name} has non-list default value: {param_field}")

        return NluIntentParameter(
            name=param_field.name,
            entity_cls=entity_cls,
            is_list=is_list,
            required=required,
            default=default
        )

@dataclass
class SessionIntentParameter(IntentParameter):
    """
    These are :class:`IntentParameter`\ s that are injected in the conversation
    by triggers and fulfillment procedre (e.g. a `delivery_info` dict can be
    sent when triggering an intent for pushing an order delivery update to
    User).
    
    Every member of an :class:`Intent` class that is annotated with a primitive
    type, :class:`list`, :class:`dict` or a :class:`dataclass` type will be
    recognized as a Session Parameter.

    Args:
        name: Parameter name
        entity_cls: Parameter type
        is_list: Parameter will match multiple values in the User utterance
        required: If True, user will be prompted for parameter value when that
            can't be tagged in his utterance
        default: If set, this value will be used when parameter value can't be
            tagged in the User's utterance
    """
    data_type: Type[T]

    def __post_init__(self):
        if not self.is_serializable():
            raise ValueError(f"Parameter {self.name} with data type {self.data_type} "
                             "is not serializable. Must be one of str, int, float, list, "
                             "dict, or a dataclass.")

    def is_serializable(self):
        """
        Return True if the Parameter specification is serializable as a string
        by :meth:`serialize_value`

        Returns:
            True if parameter is serializable as a string, False otherwise
        """
        if issubclass(self.data_type, (list, dict, int, float, str)):
             return True
        if is_dataclass_strict(self.data_type):
            return True
        return False

    def serialize_value(self, value: Any) -> str:
        """
        Serialize the given value based on `data_type`. These are the supported
        scenarios:

        * `data_type` is a JSON-serializable (:class:`list` or a :class:`dict`,
          :class:`str`, :class:`int`, :class:`float`) -> value is serialized as
          JSON
        * `data_type` is a `dataclass` -> value is converted to dict with custom
          :func:`~intents.helpers.data_classes.to_dict`. In addition to
          standard :func:`asdict` behavior, it will process Enums correctly.

        Args:
            value: The value to serialize based on the Parameter spec

        Raises:
            ValueError: If `data_type` is not serializable

        Returns:
            A string representation of `value`
        """
        if issubclass(self.data_type, (int, float, str)):
            return str(value)
        
        if issubclass(self.data_type, (list, dict)):
            return json.dumps(value)

        if is_dataclass_strict(self.data_type):
            return json.dumps(to_dict(value))

        raise ValueError(f"Data type {self.data_type} of field {self.name} is not serializable.")

    def deserialize_value(self, data: str) -> Any:
        if issubclass(self.data_type, (int, float, str)):
            return self.data_type(data)

        if issubclass(self.data_type, (list, dict)):
            return json.loads(data)

        if is_dataclass_strict(self.data_type):
            data = json.loads(data)
            return from_dict(self.data_type, data)

        raise ValueError(f"Data type {self.data_type} of field {self.name} is not serializable.")

    @staticmethod
    def from_dataclass_field(param_field: dataclasses.Field) -> "SessionIntentParameter":
        if isinstance(param_field.type, _GenericAlias):
            if param_field.type.__dict__.get('_name') == 'List':
                data_type = list
            elif param_field.type.__dict__.get('_name') == 'Dict':
                data_type = dict
            else:
                raise ValueError(f"Invalid typing '{param_field.type}' for Session parameter '{param_field.name}'. Only 'List' and 'Dict' are supported.")
        else:
            data_type = param_field.type

        required, default = _is_required(param_field)

        if not required and issubclass(data_type, list) and not isinstance(default, list):
            raise ValueError(f"List Session Parameter {param_field.name} has non-list default value: {param_field}")
            
        # Will raise ValueError if type is not compatible
        return SessionIntentParameter(
            name=param_field.name,
            data_type=data_type,
            required=required,
            default=default
        )

class ParameterSchema(dict):

    @property
    def nlu_parameters(self) -> Dict[str, NluIntentParameter]:
        """
        Return the `ParameterSchema` subset that only contains NLU Parameters

        Returns:
            A map of NLU Parameters
        """
        return {k: v for k, v in self.items() if isinstance(v, NluIntentParameter)}
    
    @property
    def session_parameters(self) -> Dict[str, SessionIntentParameter]:
        """
        Return the `ParameterSchema` subset that only contains Session Parameters

        Returns:
            A map of Session Parameters
        """
        return {k: v for k, v in self.items() if isinstance(v, SessionIntentParameter)}

def _is_required(dataclass_field: dataclasses.Field) -> Tuple[bool, Any]:
    """
    Return `(True, None)` if field is required (i.e. it has no default value),
    `(False, <DEFAULT_VALUE>)` otherwise.

    Args:
        dataclass_field: A dataclass field, as it is returned by :func:`dataclasses.field`

    Returns:
        True/False if field is required or not, and its default value
    """
    required = True
    default = None
    if not isinstance(dataclass_field.default, dataclasses._MISSING_TYPE):
        required = False
        default = dataclass_field.default
    if not isinstance(dataclass_field.default_factory, dataclasses._MISSING_TYPE):
        required = False
        default = dataclass_field.default_factory()
    return required, default
