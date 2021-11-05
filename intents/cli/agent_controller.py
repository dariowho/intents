import importlib
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Type

from intents import Agent, connectors
from intents.testing import AgentTester
from intents.connectors.interface.fulfillment import WebhookConfiguration

class ConnectorName(Enum):
    DIALOGFLOW = "dialogflow"
    ALEXA = "alexa"
    SNIPS = "snips"

# TODO: use Pydantic or something to improve configuration options and validation
    

@dataclass
class AgentController:
    
    agent_class_import: str = None
    connector: ConnectorName = "dialogflow"
    connector_parameters: dict = field(default_factory=dict) # TODO: model
    dev_server_port: int = 8000
    webhook_configuration: WebhookConfiguration = None

    def __post_init__(self):
        if isinstance(self.connector, str):
            self.connector = ConnectorName(self.connector)

    @classmethod
    def from_env(cls):
        default_conf = cls()
        conn_name, conn_parameters = cls._connector_parameters_from_env()

        agent_class_import = os.getenv("I_AGENT_CLASS_IMPORT")
        if not agent_class_import:
            raise ValueError("Env variable I_AGENT_CLASS_IMPORT is empty or unset. This is necessary to load your agent programmatically")
        
        webhook_host = os.getenv("I_WEBHOOK_HOST", None)
        webhook_token = os.getenv("I_WEBHOOK_TOKEN", None)

        return cls(
            agent_class_import=agent_class_import,
            connector=conn_name if conn_name else default_conf.connector,
            connector_parameters=conn_parameters,
            dev_server_port=int(os.getenv("I_DEV_SERVER_PORT", default_conf.dev_server_port)),
            webhook_configuration = WebhookConfiguration(webhook_host, token=webhook_token)            
        )

    @staticmethod
    def _connector_parameters_from_env():
        connector_name = os.getenv("I_CONNECTOR")
        if not connector_name:
            return None, {}

        if isinstance(connector_name, str):
            connector_name = ConnectorName(connector_name)

        if connector_name == ConnectorName.DIALOGFLOW:
            parameters = {}
            if credentials := os.getenv("I_DIALOGFLOW_CREDENTIALS"):
                parameters["google_credentials"] = credentials
            else:
                raise ValueError("Dialogflow connector is set, but no credentials are provided. Please provide them like 'I_DIALOGFLOW_CREDENTIALS=/path/to/service-account.json'")
        else:
            parameters = {}

        return connector_name, parameters

    def load_agent_cls(self) -> Type[Agent]:
        class_path_components = self.agent_class_import.split(".")
        class_module_name = ".".join(class_path_components[:-1])
        class_name = class_path_components[-1]

        agent_cls_module = importlib.import_module(class_module_name)
        agent_cls = getattr(agent_cls_module, class_name)
        assert issubclass(agent_cls, Agent)
        return agent_cls

    def load_connector(self):
        agent_cls = self.load_agent_cls()
        
        if not self.connector:
            raise ValueError("Connector parameters not found. Make sure to define necessary env variables (e.g. 'I_CONNECTOR=dialogflow'")

        if self.connector == ConnectorName.DIALOGFLOW:
            from intents.connectors import DialogflowEsConnector
            return DialogflowEsConnector(
                agent_cls=agent_cls,
                webhook_configuration=self.webhook_configuration,
                **self.connector_parameters
            )
        elif self.connector == ConnectorName.ALEXA:
            from intents.connectors._experimental.alexa import AlexaConnector
            return AlexaConnector(**self.connector_parameters)
        elif self.connector == ConnectorName.SNIPS:
            from intents.connectors._experimental.snips import SnipsConnector
            return SnipsConnector(**self.connector_parameters)

        raise ValueError(f"Connector {self.connector} is not supported. This is possibly a bug. Please file an issue on the Intents repository.")

    def load_agent_tester(self):
        return AgentTester(
            connector=self.load_connector(),
            dev_server_port=self.dev_server_port,
            dev_server_token=self.webhook_configuration.token
        )
