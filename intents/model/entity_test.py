from intents import Entity

def test_entity_default_name():

    class MyEntity(Entity):
        pass

    assert MyEntity.name == 'MyEntity'

def test_entity_custom_name():

    class MyEntity(Entity):
        name = "CustomEntityName"

    assert MyEntity.name == 'CustomEntityName'
