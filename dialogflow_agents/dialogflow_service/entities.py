from dialogflow_agents.model.entity import Sys
from dialogflow_agents.prediction_service import EntityMapping, StringEntityMapping, ServiceEntityMappings

class PersonEntityMapping(EntityMapping):
    """
    Dialogflow's `sys.person` entity type is returned as an object like
    `{"name": "Guido"}`
    """

    entity_cls = Sys.Person
    service_name = 'sys.person'

    def from_service(self, service_data: dict) -> Sys.Person:
        # Currently `to_service()` is not used in triggers
        if isinstance(service_data, str):
            service_data = {"name": service_data}
        return Sys.Person(service_data['name'])

    def to_service(self, entity: Sys.Person) -> dict:
        return {"name": str(entity)}

MAPPINGS = ServiceEntityMappings.from_list([
    StringEntityMapping(Sys.Any, "sys.any"),
    StringEntityMapping(Sys.Integer, "sys.number-integer"),
    PersonEntityMapping()
])
