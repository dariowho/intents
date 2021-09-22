"""
This module defines general purpose helpers that are used throughout the project
"""
import dataclasses
from enum import Enum
from datetime import datetime
from dataclasses import asdict, field

class CustomFields(Enum):
    OMIT_NONE = "OMIT_NONE"

def OmitNone():
    """
    TODO: OmitNone values may appear when instantiating the dataclass 
    """
    return field(default=CustomFields.OMIT_NONE)

def custom_asdict_factory():
    """
    Return a custom dict factory to use with dataclasses' :func:`asdict`. Custom
    behavior include:

    * Serialize Enums with their value
    * Omit fields whose value is OmitNone() (e.g. `foo: str = OmitNone()`)

    This is mainly used to serialize schemas in Connectors.

    source: https://stackoverflow.com/questions/61338539/how-to-use-enum-value-in-asdict-function-from-dataclasses-module
    """

    # TODO: also handle date and datetime types with de-serialization

    def result_f(data):

        def convert_value(obj):
            if isinstance(obj, Enum):
                return obj.value
            if isinstance(obj, datetime):
                return str(obj)
            return obj

        return dict((k, convert_value(v)) for k, v in data if v != CustomFields.OMIT_NONE)
    
    return result_f

def is_dataclass_strict(obj):
    """
    Like :func:`dataclasses.is_dataclass`, but return True only if the class
    itself was decorated with `@dataclass` (that is, inheriting from a parent
    dataclass is not sufficient)

    .. code-block:: python

        @dataclass
        class a_class:
            foo: str

        class a_subclass(a_class):
            bar: str

        is_dataclass(a_subclass)           # True
        is_dataclass_strict(a_subclass)    # False
    """
    cls = obj if isinstance(obj, type) else type(obj)
    return dataclasses._FIELDS in cls.__dict__

def to_dict(dataclass_obj: type) -> dict:
    """
    A wrapper around default :func:`asdict` that handles Enums via
    :func:`custom_asdict_factory`.

    Args:
        dataclass_obj: A dataclass

    Returns:
        A `dict` representation of `dataclass_obj`
    """
    return asdict(dataclass_obj, dict_factory=custom_asdict_factory())
