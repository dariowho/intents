"""
Snips NLU is an open source Python/Rust library for Natural Language Understanding.
It provides intent classification and entity (slot) tagging, and it runs **locally**
as a standard Python library.

:class:`SnipsConnector` is a Connector that doesn't require any other service
(nor remote or local) to run. It makes predictions internally, by calling the
underlying `snips-nlu` library functions.

To use :class:`SnipsConnector` it is necessary to install its optional
dependency group:

.. code-block:: sh

    pip install intents[snips]

More details about Snips can be found at

* https://github.com/snipsco/snips-nlu
* https://snips-nlu.readthedocs.io/
"""
import os
import json
import shutil
import logging
from typing import Union, Type

import snips_nlu

from intents import Intent, Agent, LanguageCode
from intents.language import agent_supported_languages, ensure_language_code
from intents.connectors.interface import Connector, ServiceEntityMappings, FulfillmentRequest
from intents.connectors._experimental.snips.prediction import SnipsPrediction, SnipsPredictionComponent
from intents.connectors._experimental.snips import entities, prediction_format

logger = logging.getLogger(__name__)

class SnipsConnector(Connector):
    """
    This is a :class:`~intents.connectors.interface.Connector` that runs entirely locally, without needing any resident
    service to operate. Predictions are made by calling the `snips-nlu` Python
    API.

    .. warning::

        `SnipsConnector` is **experimental**: expect running into relevant rough
        edges when using it. Its main limitations include:

        * Intent relations are not implemented
        * Prompts for required parameters are not implemented: an exception will be thrown if all the required parameters are not present 
        * :class:`Sys.Email`, :class:`Sys.PhoneNumber` and :class:`Url` entities are patched with empty placeholders
        * :class:`Sys.Date` is only available in English

    Args:
        agent_cls: The Agent class to train the system
        default_session: A default session identifier. Will be generated
            randomly if None
        default_language: Default language for predictions. English will be used
            if None.
    """

    entity_mappings: ServiceEntityMappings = entities.ENTITY_MAPPINGS

    nlu_engine: snips_nlu.SnipsNLUEngine = None
    prediction_component: SnipsPredictionComponent

    def __init__(self,
        agent_cls: Type[Agent],
        default_session: str=None,
        default_language: Union[LanguageCode, str]=None
    ):
        super().__init__(agent_cls, default_session, default_language)
        self.nlu_engines = {
            lang: snips_nlu.SnipsNLUEngine() for lang in agent_supported_languages(agent_cls)
        }
        self.prediction_component = SnipsPredictionComponent(agent_cls, self.entity_mappings)

    def export(self, destination: str):
        """
        Export Agent in the given folder:

        .. code-block:: python

            from example_agent.agent import ExampleAgent
            from intents.connectors._experimental.snips import SnipsConnector

            snips = SnipsConnector(ExampleAgent)
            snips.export("./TMP_SNIPS")

        The export will generate one JSON file per language, they can be loaded
        into Snips as a JSON Dataset.

        Args:
            destination: A folder that will contain exported JSON files
        """
        from intents.connectors._experimental.snips import export

        rendered = export.render(self)

        if os.path.isdir(destination):
            logger.warning("Removing existing export folder: %s", destination)
            shutil.rmtree(destination)
        os.makedirs(destination)

        for lang, data in rendered.items():
            with open(os.path.join(destination, f"agent.{lang.value}.json"), "w") as f:
                json.dump(data, f, indent=4)

    def upload(self):
        """
        As Snips runs locally as a Python library, there is no external service
        to upload the model to. Instead, `upload` will train Snips local models.

        Currently there is no persistence for trained models. This means that
        `upload` should be called every time :class:`SnipsConnector` is instantiated.
        """
        from intents.connectors._experimental.snips import export
        for lang, rendered in export.render(self).items():
            self.nlu_engines[lang].fit(rendered)

    def predict(self, message: str, session: str=None, language: Union[LanguageCode, str]=None) -> SnipsPrediction:
        """
        Predict the given User message in the given session using the given
        language. When `session` or `language` are None, `predict` will use the
        default values that are specified in :meth:`__init__`.

        *predict* will return an instance of :class:`Prediction`, representing
        the service response.

        >>> from intents.connectors._experimental.snips import SnipsConnector
        >>> from example_agent import ExampleAgent
        >>> snips = SnipsConnector(ExampleAgent)
        >>> snips.upload() # This trains the models
        >>> prediction = snips.predict("Hi, my name is Guido")
        >>> prediction.intent
        UserNameGive(user_name='Guido')
        >>> prediction.intent.user_name
        "Guido"
        >>> prediction.fulfillment_text
        "Hi Guido, I'm Bot"
        >>> prediction.confidence
        0.62

        Note that the Italian version of :class:`~example_agent.ExampleAgent`
        won't be trained, as :class:`Sys.Date` is not available for the Italian
        language in Snips.

        Args:
            message: The User message to predict
            session: Any string identifying a conversation
            language: A LanguageCode object, or a ISO 639-1 string (e.g. "en")
        """
        if not language:
            language = self.default_language
        language = ensure_language_code(language)
        parse_result_dict = self.nlu_engines[language].parse(message)
        parse_result = prediction_format.from_dict(parse_result_dict)
        prediction = self.prediction_component.prediction_from_parse_result(parse_result, language)
        return self.prediction_component.fulfill_local(prediction, language)

    def trigger(self, intent: Intent, session: str=None, language: Union[LanguageCode, str]=None) -> SnipsPrediction:
        """
        As Snips runs locally and intent relation resolution is not supported,
        Triggers don't do much more at the moment than returing the intent as it
        was passed in input.

        >>> from intents.connectors._experimental.snips import SnipsConnector
        >>> from example_agent import ExampleAgent, smalltalk
        >>> snips = SnipsConnector(ExampleAgent)
        >>> snips.upload() # This trains the models
        >>> prediction = snips.trigger(smalltalk.AgentNameGive(agent_name='Alice'))
        >>> prediction.intent
        AgentNameGive(agent_name='Alice')
        >>> prediction.fulfillment_text
        "Howdy Human, I'm Alice"
        >>> prediction.confidence
        1.0

        Args:
            intent: The Intent instance to trigger
            session: Any string identifying a conversation
            language: A LanguageCode object, or a ISO 639-1 string (e.g. "en")
        """
        if not language:
            language = self.default_language
        language = ensure_language_code(language)
        prediction = self.prediction_component.prediction_from_intent(intent, language)
        return self.prediction_component.fulfill_local(prediction, language)

    def fulfill(self, fulfillment_request: FulfillmentRequest) -> dict:
        """
        *Not implemented*
        """
        raise NotImplementedError()
