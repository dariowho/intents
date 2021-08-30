import json

from intents.helpers.logging import jsondict

def test_jsondict_str():
    d = {"foo": "bar", "a": True, "b": None}
    assert str(jsondict(d)) == json.dumps(d, indent=2)
