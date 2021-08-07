import pytest

from intents import Entity

def test_entity_default_name():

    class MyEntity(Entity):
        pass

    assert MyEntity.name == 'MyEntity'

def test_entity_custom_name():

    class MyEntity(Entity):
        name = "CustomEntityName"

    assert MyEntity.name == 'CustomEntityName'

def test_entity_reserved_name():
    with pytest.raises(ValueError):
        class I_MyEntity(Entity):
            pass

    with pytest.raises(ValueError):
        class MyEntity(Entity):
            name = "i_my_entity"
