"""
This module defines general purpose helpers that are used throughout the project
"""
from enum import Enum
from dataclasses import field

class CustomFields(Enum):
    OMIT_NONE = "OMIT_NONE"

def OmitNone():
    return field(default=CustomFields.OMIT_NONE)

def custom_asdict_factory():
    """
    Return a custom dict factory to use with dataclasses' :func:`asdict`. Custom
    behavior include:

    * Serialize Enums with their value
    * Omit fields whose value is OmitNone() (e.g. `foo: str = OmitNone()`)

    This is mainly used to serialize schemas in Connectors.

    source: https://stackoverflow.com/questions/61338539/how-to-use-enum-value-in-asdict-function-from-dataclasses-module

    TODO: add optional "exclude_none" to exclude None fields from output
    """

    def result_f(data):

        def convert_value(obj):
            if isinstance(obj, Enum):
                return obj.value
            return obj

        return dict((k, convert_value(v)) for k, v in data if v != CustomFields.OMIT_NONE)
    
    return result_f
