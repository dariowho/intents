"""
Contexts allow the Agent to interpret utterances differently depending on the
conversation state. An example of their usage can be found in
:mod:`example_agent.rickroll`.

.. warning::

    This module is **deprecated** and will be removed in 0.3. Upgrade your code to use 
    :mod:`intents.model.relations` instead.
"""
### Deprecated ###

from intents import SessionEntity

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

###############################