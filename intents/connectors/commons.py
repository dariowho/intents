"""
Some configuration classes are not service-specific. Currently the only one is
:class:`WebhookConfiguration`.
"""
from typing import Dict
from dataclasses import dataclass, field

@dataclass
class WebhookConfiguration:
    """
    Specifies connection parameters for the Agent's webhook. This is the
    endpoint that is called by services to fulfill an intent.
    """
    url: str
    headers: Dict[str, str] = field(default_factory=dict)
