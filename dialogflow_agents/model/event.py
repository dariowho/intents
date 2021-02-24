class _EventMetaclass(type):
    
    @property
    def name(cls):
        # TODO: handle CamelCase to EVENT_NAME and strip trailing "_EVENT"
        return cls.__name__.upper()

class Event(metaclass=_EventMetaclass):
    """
    This is a base class for an Event

    .. code-block:: python

        class welcome(Event):
            \"\"\"
            This is an external event that is triggered on the Agent 
            by an external source.
            \"\"\"

    Events names are rendered in Dialogflow with their upper case class name.
    The example above will produce a `WELCOME` event in the intent that
    references it.
    """
    pass
