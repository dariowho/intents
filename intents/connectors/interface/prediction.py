import logging
import warnings
from dataclasses import dataclass, field

from intents import Intent
from intents.language import IntentResponseDict

logger = logging.getLogger(__name__)

@dataclass
class Prediction:
    """
    One of the core uses of Service Connectors is to predict user utterances, or
    programmatically trigger intents. This class models the result of such
    predictions and triggers.

    You will typically obtain `Prediction` objects from :class:`Connector`
    methods :meth:`~Connector.predict` and :meth:`~Connector.trigger`.

    Args:
        intent: An instance of the predicted Intent
        confidence: A confidence value on the service prediction
        fulfillment_messages: A map of Intent Responses, as they were
            returned by the Service.
        fulfillment_text: A plain-text version of the response
    """
    intent: Intent
    confidence: float
    fulfillment_messages: IntentResponseDict = field(repr=False)
    fulfillment_text: str = None

    @property
    def fulfillment_message_dict(self):
        warnings.warn("Prediction.fulfillment_message_dict is deprecated. Please update "
                      "your code to use Prediction.fulfillment_messages instead.", DeprecationWarning)
        return self.fulfillment_messages
