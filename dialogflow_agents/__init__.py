from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

class SessionEntity:

    _session = None

    def to(self, session: str):
        self._session = session
        return self

from dialogflow_agents.model.intent import Intent
from dialogflow_agents.model.entity import Entity, Sys
from dialogflow_agents.model.context import Context
from dialogflow_agents.model.event import Event
from dialogflow_agents.model.agent import Agent
from dialogflow_agents.prediction_service import PredictionService
