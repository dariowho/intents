from __future__ import annotations

import sys
import uuid
import logging
import threading
from time import sleep
from typing import Any, ClassVar, Iterable, List, Union
from dataclasses import dataclass, field

from intents import Intent
from intents.connectors.interface import Connector, TestableConnector
from intents.connectors.interface.prediction import Prediction
from intents.connectors.interface.testing import RecordedFulfillmentCall
from intents.fulfillment import run_dev_server

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
class IntentAssert:
    name: str = None
    param_dict: dict = field(default_factory=dict)

    def assert_intent(self, intent: Intent):
        if self.name:
            _assert_value(intent.name, self.name)
        if self.param_dict:
            param_dict = intent.parameter_dict()
            for k, v in self.param_dict.items():
                _assert_value(param_dict[k], v)

    @classmethod
    def from_intent(cls, intent: Intent):
        return cls(
            name=intent.name,
            param_dict=intent.parameter_dict()
        )

@dataclass
class PredictionAssert(IntentAssert):
    
    def assert_prediction(self, prediction: Prediction):
        super().assert_intent(prediction.intent)

@dataclass
class FulfillmentAssert(IntentAssert):
    
    def assert_fulfillment(self, recorded_call: RecordedFulfillmentCall):
        super().assert_intent(recorded_call.intent)

@dataclass
class TestingStoryStep:
    utterance: str
    prediction_assert: List[PredictionAssert]
    fulfillment_asserts: List[FulfillmentAssert]
    # callable_asserts: List[Callable] = None

    __test__ = False

@dataclass
class TestingStory:
    connector: Connector
    steps_wait: float
    session_id: str = field(default_factory=lambda: f"intents-test-{uuid.uuid1()}")
    
    __test__ = False

    def step(
        self,
        utterance_or_step: Union[str, TestingStoryStep],
        prediction_assert: Union[PredictionAssert, Intent]=None,
        fulfill_asserts: Union[FulfillmentAssert, Intent, Iterable[Union[FulfillmentAssert, Intent]]]=None,
        # callable_asserts: List[Callable]=None 
    ):
        if isinstance(utterance_or_step, str):
            if isinstance(prediction_assert, Intent):
                prediction_assert = PredictionAssert.from_intent(prediction_assert)
            if not fulfill_asserts:
                fulfill_asserts = []
            if not isinstance(fulfill_asserts, Iterable):
                fulfill_asserts = [fulfill_asserts]
            fulfill_asserts = [FulfillmentAssert.from_intent(x) if isinstance(x, Intent) else x for x in fulfill_asserts]
            step = TestingStoryStep(utterance_or_step, prediction_assert, fulfill_asserts)
        else:
            assert isinstance(utterance_or_step, TestingStoryStep)
            assert not prediction_assert
            assert not fulfill_asserts
            step = utterance_or_step

        # Do prediction
        prediction = self.connector.predict(step.utterance, self.session_id)
        
        # Test prediction result
        if step.prediction_assert:
            logger.info("Checking prediction %s against assert %s", prediction, step.prediction_assert)
            step.prediction_assert.assert_prediction(prediction)

        # Test fulfillment calls
        if isinstance(self.connector, TestableConnector):
            fulfillment_calls = self.connector.recorded_fulfillment_calls[self.session_id]
            for fulfill_assert in step.fulfillment_asserts:
                if not fulfillment_calls:
                    AssertionError(f"Fulfillment assert {fulfill_assert} cannot be satisfied, as there are no recorded fulfillment calls left.")
                recorded_call = fulfillment_calls.pop(0)
                logger.info("Checking fulfillment call %s against assert %s", recorded_call, fulfill_assert)
                fulfill_assert.assert_fulfillment(recorded_call)
            self.connector.recorded_fulfillment_calls[self.session_id].clear()
        
        sleep(self.steps_wait)
        

@dataclass
class AgentTester:
    connector: Connector
    steps_wait: float = 0.5
    # parrallel_n: int = 1
    dev_server: bool = True
    dev_server_port: int = 8000
    dev_server_token: str = None

    _dev_server_thread: ClassVar[threading.Thread] = None

    def __post_init__(self):
        if isinstance(self.connector, TestableConnector):
            self.connector.is_recording_enabled = True
        else:
            logger.warning("Connector %s is not an instance of TestableConnector. Fulfillment Asserts will not be processed")
        self.ensure_server()

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
            self._dev_server_thread.daemon = True
            self._dev_server_thread.start()
            sleep(3)
            self._check_dev_thread()
            # TODO: test that connector is receiving fulfillment requests

    def _check_dev_thread(self):
        if self.dev_server and not self._dev_server_thread.is_alive():
            self._dev_server_thread.join()
            sys.stdout.flush()
            sys.stderr.flush()
            raise ValueError("Dev server thread died")

    def story(self):
        return TestingStory(self.connector, self.steps_wait)
