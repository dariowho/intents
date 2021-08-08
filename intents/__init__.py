from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

__version__ = "0.3.dev1"

class SessionEntity:

    _session = None

    def to(self, session: str):
        self._session = session
        return self

from intents.model.intent import Intent
from intents.model.entity import Entity, Sys
from intents.model.agent import Agent
from intents.model.relations import follow
from intents.model.fulfillment import FulfillmentRequest, FulfillmentResponse

from intents.language import LanguageCode
