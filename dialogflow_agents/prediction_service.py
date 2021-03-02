from abc import ABC, abstractmethod
from dataclasses import dataclass

from dialogflow_agents import Intent

@dataclass
class Prediction:
    """
    This class is meant to abstract prediction results from a generic Prediction
    Service. It uses names from Dialogflow, as it is currently the only
    supported service
    """
    intent_name: str
    confidence: str
    contexts: dict
    parameters_dict: dict
    fulfillment_messages: dict
    fulfillment_text: str = None

class PredictionService(ABC):
    """
    This is the interface that Prediction Services must implement to integrate
    with Agents.
    """

    _agent: 'dialogflow_agents.Agent'

    @abstractmethod
    def predict_intent(self, message: str) -> Intent:
        """
        Predict the Intent from the given User message

        :param message: The message to be classified
        """
    
    @abstractmethod
    def trigger_intent(self, intent: Intent) -> Intent:
        """
        Trigger the given Intent and return the Service response.

        Note that the response is an Intent object as well. However, it will
        bear an additional `prediction` field, containing details such as
        confidence, fulfillment messages etc.
        """

    def _prediction_to_intent(self, prediction: Prediction) -> Intent:
        """
        Turns a Prediction object into an Intent
        """
        intent_class = self._agent._intents_by_name.get(prediction.intent_name)
        if not intent_class:
            # TODO: error refers to Dialogflow
            raise ValueError(f"Prediction returned intent '{prediction.intent_name}', but this was not found in Agent definition. Make sure to restore a latest Agent export from `dialogflow_service.export.export()`. If the problem persists, please file a bug on the Dialoglfow Agents repository.")
        return intent_class.from_prediction(prediction)
