import abc
from dataclasses import dataclass
from typing import List, Dict, Any

from intents import Intent

# @dataclass
# class StoredIntent:
#     name: str
#     parameter_dict: Dict[str, Any]
#     lifespan: int

# class StoredIntentStack:
#     _stack: List[Intent]
#     _intents_by_name: Dict[str, Intent]

#     def __init__(self):
#         self._stack = []

@dataclass
class Session:
    """
    Session Persistence layer interface
    """
    session_id: str
    intents_history: List[Intent]

    def global_params(self):
        result = {}
        for intent in self.intents_history:
            if intent.lifespan > 0:
                result.update(intent.parameter_dict())
        return result

    def update(self, new_intent: Intent):
        new_history = []
        for intent in self.intents_history:
            # TODO: replace lifespans if `new_lifespan`
            new_history.append(intent.replace(lifespan=intent.lifespan-1))
        new_history.append(new_intent)
        return Session(self.session_id, new_history)

class SessionStorage(abc.ABC):

    @abc.abstractmethod
    def read(self, session_id: str):
        pass

    @abc.abstractmethod
    def write(self, session: Session):
        pass

    @abc.abstractmethod
    def delete(self, session_id: str):
        pass

    @abc.abstractmethod
    def destroy(self):
        pass

class InMemorySessionStorage(SessionStorage):
    
    _sessions: Dict[str, Session]

    def __init__(self):
        _sessions = {}

    def read(self, session_id: str):
        return self._sessions.get(session_id)

    def write(self, session: Session):
        self._sessions[session.session_id] = session

    def delete(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]

    def destroy(self):
        self._sessions = {}
