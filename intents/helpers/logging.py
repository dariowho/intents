import json

class jsondict(dict):
    """
    A dictionary that is serialized to JSON when casted to `str`. This is
    convenient in logs.
    """

    def __str__(self):
        return json.dumps(self, indent=2)

    def __repr__(self):
        return self.__str__()
