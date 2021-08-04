import pytest

from intents.model.names import check_name

def test_check_name():
    check_name("valid_intent_name")
    check_name("AlsoValidName")
    check_name("valid.NameAsWell")
    with pytest.raises(ValueError):
        check_name("Invalid Name")
    with pytest.raises(ValueError):
        check_name("invalid $name")
    with pytest.raises(ValueError):
        check_name("invalid__Name")
    with pytest.raises(ValueError):
        check_name("_InvalidName")
    with pytest.raises(ValueError):
        check_name("i_InvalidName")
