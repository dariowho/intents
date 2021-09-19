from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

__version__ = "0.3.0"

class SessionEntity:

    _session = None

    def to(self, session: str):
        self._session = session
        return self

from intents.language_codes import LanguageCode

from intents.model.intent import Intent, FulfillmentContext, FulfillmentResult
from intents.model.entity import Entity, EntityMixin, Sys
from intents.model.agent import Agent
from intents.model.relations import follow
