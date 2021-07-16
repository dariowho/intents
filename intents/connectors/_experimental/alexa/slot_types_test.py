from intents import Sys
from intents.connectors._experimental.alexa.slot_types import ENTITY_MAPPINGS

def test_date_mapping():
    entity_type = Sys.Date
    entity_value = "2021-07-11"
    mapping = ENTITY_MAPPINGS[entity_type]
    assert mapping.from_service(entity_value) == Sys.Date(2021, 7, 11)
    assert mapping.to_service(Sys.Date(2021, 7, 11)) == entity_value
