from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

__version__ = "0.1.dev2"

class SessionEntity:

    _session = None

    def to(self, session: str):
        self._session = session
        return self

from intents.model.intent import Intent
from intents.model.entity import Entity, Sys
from intents.model.context import Context
from intents.model.event import Event
from intents.model.agent import Agent

from intents.language import LanguageCode
