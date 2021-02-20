from dialogflow_agents import SessionEntity

class _ContextMetaclass(type):
    """
    This is just used to set a `name` attribute on the Context class
    """

    @property
    def name(cls):
        return cls.__name__

class Context(SessionEntity, metaclass=_ContextMetaclass):
    """
    Context subclasses are generated from the Dialogflow agent. The name of the class corresponds to the name of the context.

    >>> c_greetings.name
    'c_greetings'
    >>> c_greetings().name
    'c_greetings'
    """

    lifespan: int = None

    def __init__(self, lifespan):
        self.lifespan = lifespan

    @property
    def name(self):
        return self.__class__.name
