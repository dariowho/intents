import os
import json
import shutil
import logging
import tempfile

import snips_nlu

from intents import LanguageCode
from intents.model.agent import _AgentMetaclass
from intents.model.entity import _EntityMetaclass
from intents.service_connector import Connector, ServiceEntityMappings
from intents.connectors._experimental.snips import entities, prediction_format

logger = logging.getLogger(__name__)

class SnipsConnector(Connector):

    entity_mappings: ServiceEntityMappings = entities.ENTITY_MAPPINGS

    nlu_engine: snips_nlu.SnipsNLUEngine = None

    def __init__(self,
        agent_cls: _AgentMetaclass,
        default_session: str=None,
        default_language: str=None
    ):
        super().__init__(agent_cls, default_session, default_language)
        self.nlu_engine = snips_nlu.SnipsNLUEngine()

    def export(self, destination: str):
        """
        Export Agent in the given folder:

        .. code-block:: python

            from example_agent.agent import ExampleAgent
            from intents.connectors._experimental.snips import SnipsConnector

            snips = SnipsConnector(ExampleAgent, "any invocation")
            snips.export("./TMP_SNIPS")

        The export will generate one JSON file per language, they can be loaded
        into Snips as a JSON Dataset.
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
        from intents.connectors._experimental.snips import export
        rendered = export.render(self)
        self.nlu_engine.fit(rendered[LanguageCode.ENGLISH])

    def fulfill(self):
        raise NotImplementedError()

    def predict(self, message: str, lang: LanguageCode=LanguageCode.ENGLISH):
        from intents.connectors._experimental.snips import prediction
        parse_result_dict = self.nlu_engine.parse(message)
        parse_result = prediction_format.from_dict(parse_result_dict)
        return prediction.prediction_from_parse_result(self, parse_result, lang)

    def trigger(self):
        raise NotImplementedError()

    def _entity_service_name(self, entity_cls: _EntityMetaclass):
        return self.entity_mappings[entity_cls.name].service_name