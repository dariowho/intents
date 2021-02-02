from dataclasses import dataclass

class StringParameter(str):
    """
    This is the field type that will be used in dataclasses. We define a
    supertype here, so that it's easy to check that user intents declare types
    that come from Entities
    """
    df_entity: "AnyEntity" = None
    df_parameter_value: str = None

@dataclass
class AnyEntity:
    name: str

    def __call__(self, value=None):

        class _StringParameter(StringParameter):
            df_entity = self
            df_parameter_value = value

        result = _StringParameter
        return result

@dataclass
class CustomEntity(AnyEntity):
    use_synonims: bool = True
    regexp_entity: bool = False
    automated_expansion: bool = False
    fuzzy_matching: bool = False
    
    system_entity = False

@dataclass
class SystemEntity(AnyEntity):

    system_entity = True

# For our users, these are just Entities
Entity = CustomEntity
