from unittest.mock import patch
from typing import Dict, Any, List
from dataclasses import dataclass, field

import pytest

from intents import Intent, Sys, Entity, follow
from intents.model.intent import ParameterSchema, SessionIntentParameter, NluIntentParameter

#
# Parameter Schema
#

def test_param_schema_no_params():

    class no_param_intent(Intent):
        """Simple Intent with no parameters"""

    assert no_param_intent.parameter_schema == {}

def test_param_scheme_with_nlu_params():

    @dataclass
    class IntentWithNluParams(Intent):
        """Intent with NLU parameters"""
        required_param: Sys.Person
        required_list_param: List[Sys.Person]
        optional_param: Sys.Person = "John"
        optional_list_param: List[Sys.Person] = field(default_factory=lambda: ["Al", "John"])

    assert IntentWithNluParams.parameter_schema == {
        "required_param": NluIntentParameter(
            name="required_param",
            entity_cls=Sys.Person,
            is_list=False,
            required=True,
            default=None
        ),
        "required_list_param": NluIntentParameter(
            name="required_list_param",
            entity_cls=Sys.Person,
            is_list=True,
            required=True,
            default=None
        ),
        "optional_param": NluIntentParameter(
            name="optional_param",
            entity_cls=Sys.Person,
            is_list=False,
            required=False,
            default="John"
        ),
        "optional_list_param": NluIntentParameter(
            name="optional_list_param",
            entity_cls=Sys.Person,
            is_list=True,
            required=False,
            default=["Al", "John"]
        ),
    }

def test_param_schema_with_session_params():
    @dataclass
    class IntentWithSessionParams(Intent):
        """Intent with Session parameters"""
        required_int: int
        required_dict: dict
        optional_dict_proxy: Dict[str, List[Any]] = field(default_factory=dict)

    assert IntentWithSessionParams.parameter_schema == {
        "required_int": SessionIntentParameter(
            name="required_int",
            data_type=int,
            required=True,
            default=None
        ),
        "required_dict": SessionIntentParameter(
            name="required_dict",
            data_type=dict,
            required=True,
            default=None
        ),
        "optional_dict_proxy": SessionIntentParameter(
            name="optional_dict_proxy",
            data_type=dict,
            required=False,
            default={}
        )
    }

def test_param_schema_with_mixed_params():
    @dataclass
    class IntentWithMixedParams(Intent):
        """Intent with NLU and Session parameters"""
        required_nlu_param: Sys.Person
        required_nlu_list_param: List[Sys.Person]
        required_session_int: int
        required_session_dict: dict
        
        optional_nlu_param: Sys.Person = "John"
        optional_nlu_list_param: List[Sys.Person] = field(default_factory=lambda: ["Al", "John"])
        optional_session_dict_proxy: Dict[str, List[Any]] = field(default_factory=dict)

    assert IntentWithMixedParams.parameter_schema == {
        "required_nlu_param": NluIntentParameter(
            name="required_nlu_param",
            entity_cls=Sys.Person,
            is_list=False,
            required=True,
            default=None
        ),
        "required_nlu_list_param": NluIntentParameter(
            name="required_nlu_list_param",
            entity_cls=Sys.Person,
            is_list=True,
            required=True,
            default=None
        ),
        "optional_nlu_param": NluIntentParameter(
            name="optional_nlu_param",
            entity_cls=Sys.Person,
            is_list=False,
            required=False,
            default="John"
        ),
        "optional_nlu_list_param": NluIntentParameter(
            name="optional_nlu_list_param",
            entity_cls=Sys.Person,
            is_list=True,
            required=False,
            default=["Al", "John"]
        ),
        "required_session_int": SessionIntentParameter(
            name="required_session_int",
            data_type=int,
            required=True,
            default=None
        ),
        "required_session_dict": SessionIntentParameter(
            name="required_session_dict",
            data_type=dict,
            required=True,
            default=None
        ),
        "optional_session_dict_proxy": SessionIntentParameter(
            name="optional_session_dict_proxy",
            data_type=dict,
            required=False,
            default={}
        )
    }
        
def test_param_schema_invalid_list_default():
    
    with pytest.raises(ValueError):

        class intent_with_invalid_list_default(Intent):
            """Intent with parameters"""
            optional_list_param: List[Sys.Person] = 42

        intent_with_invalid_list_default.parameter_schema

def test_parameter_schema_class_property():
    @dataclass
    class intent_with_params(Intent):
        """Intent with parameters"""
        required_param: Sys.Person
        required_list_param: List[Sys.Person]
        optional_param: Sys.Person = "John"
        optional_list_param: List[Sys.Person] = field(default_factory=lambda: ["Al", "John"])
        
    intent_instance = intent_with_params(required_param=None, required_list_param=None)
    assert intent_with_params.parameter_schema == intent_instance.parameter_schema

def test_parameter_schema_skips_related_intents():
    class PaymentMethod(Entity):
        pass

    @dataclass
    class ask_pay(Intent):
        pass
        
    @dataclass
    class confirm_payment(Intent):
        customer_name: Sys.Person
        contact_numbers: List[Sys.PhoneNumber]
        payment_method: PaymentMethod

        parent_ask_pay: ask_pay = follow()

    expected = {
        'customer_name': NluIntentParameter(name='customer_name', entity_cls=Sys.Person, is_list=False, required=True, default=None),
        'contact_numbers': NluIntentParameter(name='contact_numbers', entity_cls=Sys.PhoneNumber, is_list=True, required=True, default=None),
        'payment_method': NluIntentParameter(name='payment_method', entity_cls=PaymentMethod, is_list=False, required=True, default=None)
    }
    assert confirm_payment.parameter_schema == expected

#
# Misc
#

def test_dataclass_not_applied_twice():
    """https://github.com/dariowho/intents/issues/10"""
    def custom_dataclass(*args, **kwargs):
        custom_dataclass.dataclass_called += 1
    custom_dataclass.dataclass_called = 0

    with patch("intents.model.intent.dataclass", custom_dataclass):
        @custom_dataclass
        class a_class(Intent):
            foo: Sys.Integer = 42
            bar: List[Sys.Integer] = field(default_factory=lambda: [])

        assert custom_dataclass.dataclass_called == 1

def test_warning_if_superclass_not_dataclass():
    @dataclass
    class an_intent(Intent):
        foo: List[Sys.Integer] = field(default_factory=lambda: [])

    class a_sub_intent(an_intent):
        bar: Sys.Integer = 42

    with pytest.warns(None):
        @dataclass
        class a_sub_sub_intent(a_sub_intent):
            babar: Sys.Integer = 43

def test_parent_intents():
    @dataclass
    class BaseIntent(Intent):
        pass

    @dataclass
    class SubIntent(BaseIntent):
        pass

    @dataclass
    class SubSubIntent(SubIntent):
        pass

    assert BaseIntent.parent_intents() == []
    assert SubIntent.parent_intents() == [BaseIntent]
    assert SubSubIntent.parent_intents() == [SubIntent, BaseIntent]

def test_parent_intents__multiple_inheritance():
    @dataclass
    class BaseIntent(Intent):
        pass

    @dataclass
    class OtherBaseIntent(Intent):
        pass

    @dataclass
    class SubIntent(BaseIntent, OtherBaseIntent, int):
        pass

    @dataclass
    class SubSubIntent(SubIntent):
        pass

    assert SubIntent.parent_intents() == [BaseIntent, OtherBaseIntent]
    assert SubSubIntent.parent_intents() == [SubIntent, BaseIntent, OtherBaseIntent]

def test_replace_lifespan():
    @dataclass
    class MockIntent(Intent):
        lifespan = 42

    i_before = MockIntent()
    i_after = i_before.replace(lifespan=24)

    assert i_before.lifespan == 42
    assert i_after.lifespan == 24

def test_replace_lifespan_and_parameters():
    @dataclass
    class MockIntent(Intent):
        lifespan = 42
        foo: str

    i_before = MockIntent("a string")
    i_after = i_before.replace(foo="another string", lifespan=24)

    assert i_before.lifespan == 42
    assert i_before.foo == "a string"
    assert i_after.lifespan == 24
    assert i_after.foo == "another string"

# def subclass_checks_base_class_parameters():
