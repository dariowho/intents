from __future__ import annotations

import uuid
import logging
import threading
from time import sleep
from typing import Any, Callable, ClassVar, List, Union
from dataclasses import dataclass, field, fields

from intents import Intent
from intents import fulfillment
from intents.connectors.interface import Connector, TestableConnector
from intents.connectors.interface.prediction import Prediction
from intents.connectors.interface.testing import RecordedFulfillmentCall
from intents.fulfillment import run_dev_server
from intents.language_codes import LanguageCode

logger = logging.getLogger(__name__)

class StaticSentinel:

    def __init__(self):
        raise ValueError("Do not instantiate sentinels. Use it like {..., 'foo': IsNone, ...}")

class IsNone:
    pass

class IsNotNone:
    pass

def _assert_value(value: Any, expected: Any):
    if expected is IsNone:
        assert value is None
    elif expected is IsNone:
        assert value is None
    else:
        assert value == expected

@dataclass
class AssertIntent:
    name: str = None
    parameter_dict: dict = field(default_factory=dict)

    def assert_intent(self, intent: Intent):
        if self.name:
            _assert_value(intent.name, self.name)
        if self.parameter_dict:
            param_dict = intent.parameter_dict()
            for k, v in self.parameter_dict.items():
                _assert_value(param_dict[k], v)

@dataclass
class AssertPredict(AssertIntent):
    
    def assert_prediction(self, prediction: Prediction):
        super().assert_intent(prediction.intent)

@dataclass
class AssertFulfill(AssertIntent):
    
    def assert_fulfillment(self, recorded_call: RecordedFulfillmentCall):
        super().assert_intent(recorded_call.intent)

@dataclass
class TestStoryStep:
    utterance: str
    fulfillment_asserts: List[AssertFulfill]
    predict_asserts: List[AssertPredict]
    # function_asserts: List[Callable] = None


@dataclass
class TestStory:
    parent_tester: AgentTester
    session_id: str = field(default_factory=lambda: f"intents-test-{uuid.uuid1()}")

    # _failed: bool = field(default=False, init=False)

    def step(self, utterance_or_step: Union[str, TestStoryStep], *asserts):
        if isinstance(utterance_or_step, str):
            fulfillment_asserts = []
            predict_asserts = []
            for assert_object in asserts:
                if isinstance(assert_object, AssertFulfill):
                    fulfillment_asserts.append(assert_object)
                else:
                    assert isinstance(assert_object, AssertPredict)
                    predict_asserts.append(assert_object)
            step = TestStoryStep(utterance_or_step, fulfillment_asserts, predict_asserts)
        else:
            assert isinstance(utterance_or_step, TestStoryStep)
            step = utterance_or_step

        prediction = self.parent_tester.connector.predict(step.utterance, self.session_id)
        fulfillment_calls = self.parent_tester.connector.recorded_fulfillment_calls[self.session_id]
        for predict_assert in step.predict_asserts: # TODO: probably it doesn't make sense to have more than one
            predict_assert.assert_prediction(prediction)
        for fulfill_assert in step.fulfillment_asserts:
            if not fulfillment_calls:
                AssertionError(f"Fulfillment assert {fulfill_assert} cannot be satisfied, as there are no recorded fulfillment calls left.")
            recorded_call = fulfillment_calls.pop()
            fulfill_assert.assert_fulfillment(recorded_call)
        self.parent_tester.connector.recorded_fulfillment_calls[self.session_id].clear()
        sleep(self.parent_tester.steps_wait)
        

@dataclass
class AgentTester:
    connector: TestableConnector
    steps_wait: float = 0.1
    # parrallel_n: int = 1
    dev_server: bool = True
    dev_server_port: int = 8000
    dev_server_token: str = None

    _dev_server_thread: ClassVar[threading.Thread] = None

    def __post_init__(self):
        if not isinstance(self.connector, TestableConnector):
            raise ValueError(f"Connector {self.connector} does not implement the TestableConnector interface. Try using built-in DialogflowEsConnector instead.")

    def ensure_server(self):
        if not self.dev_server:
            return

        if self._dev_server_thread is None:
            print("Starting background dev server")
            self._dev_server_thread = threading.Thread(
                target=run_dev_server,
                name="AgentTester Background Server",
                kwargs={
                    'connector': self.connector,
                    'token': self.dev_server_token,
                    'port': self.dev_server_port
                }
            )
            self._dev_server_thread.start()
            # TODO: test that connector is receiving fulfillment requests

    def story(self):
        return TestStory(self)
