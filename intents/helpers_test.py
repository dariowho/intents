from enum import Enum
from dataclasses import dataclass, asdict

from intents.helpers.data_classes import custom_asdict_factory, OmitNone

def test_custom_asdict_enums_are_converted():
    class ToyEnum(Enum):
        ONE = "one"
        TWO = "two"

    @dataclass
    class ToyDataclass:
        foo: str
        enum: ToyEnum

    dc = ToyDataclass("bar", ToyEnum.TWO)
    expected = {
        "foo": "bar",
        "enum": "two"
    }

    assert asdict(dc, dict_factory=custom_asdict_factory()) == expected

def test_custom_asdict_omit_none():
    @dataclass
    class ToyDataclass:
        foo: str = OmitNone()

    dc = ToyDataclass("bar")
    expected = {
        "foo": "bar",
    }
    assert asdict(dc, dict_factory=custom_asdict_factory()) == expected

    dc = ToyDataclass(None)
    expected = {
        "foo": None,
    }
    assert asdict(dc, dict_factory=custom_asdict_factory()) == expected

    dc = ToyDataclass()
    expected = {}
    assert asdict(dc, dict_factory=custom_asdict_factory()) == expected

def test_custom_asdict_omit_none_multiple():
    @dataclass
    class ToyDataclassOne:
        foo: str = OmitNone()

    @dataclass
    class ToyDataclassTwo:
        bar: str = OmitNone()

    dc = ToyDataclassOne()
    expected = {}
    assert asdict(dc, dict_factory=custom_asdict_factory()) == expected

    dc = ToyDataclassTwo()
    expected = {}
    assert asdict(dc, dict_factory=custom_asdict_factory()) == expected
