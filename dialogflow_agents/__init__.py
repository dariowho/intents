from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

class SessionEntity:

    _session = None

    def to(self, session: str):
        self._session = session
        return self

from dialogflow_agents.intent import Intent
from dialogflow_agents.context import Context
from dialogflow_agents.agent.model import Agent
