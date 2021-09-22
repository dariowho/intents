from typing import List, Dict
from dataclasses import dataclass, fields

import pytest

from intents import Sys
from intents.model.parameter import NluIntentParameter, SessionIntentParameter, ParameterSchema

def test_param_schema_structure__is_dict_equivalent():
    ps = ParameterSchema({
        'foo': NluIntentParameter(name='foo', is_list=False, required=True, default=None, entity_cls=Sys.Integer),
        'bar': SessionIntentParameter(name='foo', required=True, default=None, data_type=dict)
    })

    assert ps == {
        'foo': NluIntentParameter(name='foo', is_list=False, required=True, default=None, entity_cls=Sys.Integer),
        'bar': SessionIntentParameter(name='foo', required=True, default=None, data_type=dict)
    }

def test_param_schema_structure__params_are_filtered():
    ps = ParameterSchema({
        'foo': NluIntentParameter(name='foo', is_list=False, required=True, default=None, entity_cls=Sys.Integer),
        'bar': SessionIntentParameter(name='foo', required=True, default=None, data_type=dict)
    })
    assert ps.nlu_parameters == {'foo': NluIntentParameter(name='foo', is_list=False, required=True, default=None, entity_cls=Sys.Integer)}
    assert ps.session_parameters == {'bar': SessionIntentParameter(name='foo', required=True, default=None, data_type=dict)}
    
    ps = ParameterSchema({
        'foo': NluIntentParameter(name='foo', is_list=False, required=True, default=None, entity_cls=Sys.Integer)
    })
    assert ps.nlu_parameters == {'foo': NluIntentParameter(name='foo', is_list=False, required=True, default=None, entity_cls=Sys.Integer)}
    assert ps.session_parameters == {}
    
    ps = ParameterSchema({
        'bar': SessionIntentParameter(name='foo', required=True, default=None, data_type=dict)
    })
    assert ps.nlu_parameters == {}
    assert ps.session_parameters == {'bar': SessionIntentParameter(name='foo', required=True, default=None, data_type=dict)}

def test_session_parameter_checks_serializable():
    class AnyCustomClass:
        pass

    with pytest.raises(ValueError):
        SessionIntentParameter(name="foo", data_type=AnyCustomClass, required=False, default=None)

def test_session_parameter_serialize_json():
    p = SessionIntentParameter(name="foo", data_type=int, required=False, default=None)
    assert p.serialize_value(42) == "42"

    p = SessionIntentParameter(name="foo", data_type=float, required=False, default=None)
    assert p.serialize_value(42.24) == "42.24"

    p = SessionIntentParameter(name="foo", data_type=list, required=False, default=None)
    assert p.serialize_value([1, 2, 'foo']) == '[1, 2, "foo"]'

    p = SessionIntentParameter(name="foo", data_type=dict, required=False, default=None)
    assert p.serialize_value({'foo': [1, 2, 'bar']}) == '{"foo": [1, 2, "bar"]}'

def test_session_parameter_deserialize_json():
    p = SessionIntentParameter(name="foo", data_type=int, required=False, default=None)
    assert p.deserialize_value("42")

    p = SessionIntentParameter(name="foo", data_type=float, required=False, default=None)
    assert p.deserialize_value("42.24") == 42.24

    p = SessionIntentParameter(name="foo", data_type=list, required=False, default=None)
    assert p.deserialize_value('[1, 2, "foo"]') == [1, 2, 'foo']

    p = SessionIntentParameter(name="foo", data_type=dict, required=False, default=None)
    assert p.deserialize_value('{"foo": [1, 2, "bar"]}') == {'foo': [1, 2, 'bar']}
    
def test_session_parameter_handles_proxy_types():
    @dataclass
    class Foo:
        dict_simple: dict
        dict_proxy: Dict[str, int]
        list_simple: list
        list_proxy: List[int]

    fields_dict = {f.name: f for f in fields(Foo)}

    param_dict_simple = SessionIntentParameter.from_dataclass_field(fields_dict["dict_simple"])
    param_dict_proxy = SessionIntentParameter.from_dataclass_field(fields_dict["dict_proxy"])
    assert param_dict_simple.data_type == param_dict_proxy.data_type

    serialized_dict_simple = param_dict_simple.serialize_value({"foo": 42})
    serialized_dict_proxy = param_dict_proxy.serialize_value({"foo": 42})
    assert serialized_dict_simple == serialized_dict_proxy

    deserialized_dict_simple = param_dict_simple.deserialize_value('{"foo": 42}')
    deserialized_dict_proxy = param_dict_proxy.deserialize_value('{"foo": 42}')
    assert deserialized_dict_simple == deserialized_dict_proxy

    param_list_simple = SessionIntentParameter.from_dataclass_field(fields_dict["list_simple"])
    param_list_proxy = SessionIntentParameter.from_dataclass_field(fields_dict["list_proxy"])
    assert param_list_simple.data_type == param_list_proxy.data_type
    
    serialized_list_simple = param_list_simple.serialize_value([1, 2, 'three'])
    serialized_list_proxy = param_list_proxy.serialize_value([1, 2, 'three'])
    assert serialized_list_simple == serialized_list_proxy

    deserialized_list_simple = param_list_simple.deserialize_value('[1, 2, "three"]')
    deserialized_list_proxy = param_list_proxy.deserialize_value('[1, 2, "three"]')
    assert deserialized_list_simple == deserialized_list_proxy
