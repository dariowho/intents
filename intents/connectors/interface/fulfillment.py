"""
The :class:`FulfillmentRequest` and :class:`WebhookConfiguration` classes are
used in fulfillment resolution.
"""
import logging
from typing import Dict
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

TOKEN_HEADER = "X-Intents-Token"

@dataclass
class FulfillmentRequest:
    """
    The purpose of this class is to uniform fulfillment request payloads, with
    respect to the protocol or framework they are sent with (REST, websocket,
    lambda, ...) 

    Note that the actual parsing comes later, when a :class:`Connector` receives
    the Request, and models it as a :class:`FulfillmentContext`.

    Also, it is not necessary to model a `FulfillmentResponse` counterpart: we
    can assume any fulfillment response can be modeled with a JSON-serializable
    dict.

    Args:
        body: A dict representing the request body
        headers: An optional dict containing the request headers, if present
    """
    body: dict
    headers: dict = field(default_factory=dict)

@dataclass
class WebhookConfiguration:
    """
    Specifies connection parameters for the Agent's webhook. This is the
    endpoint that is called by services to fulfill an intent.

    Args:
        url: An URL to call for fulfillments. Services may require it to be
            HTTPS
        token: An auth token that should be used to validate incoming requests.
            If set, it will be included in `headers` as `X-Intents-Token`
        headers: Headers to include in fulfillment requests. Not all services
            may support this
    """
    url: str
    token: str = None
    headers: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if self.token:
            if self.headers.get(TOKEN_HEADER):
                logger.warning("Token set in WebhookConfiguration. However, a "
                               "'%s' header is also set: it will be "
                               "overwritten with the specified token value", TOKEN_HEADER)
            self.headers[TOKEN_HEADER] = self.token
