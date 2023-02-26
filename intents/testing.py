"""
While unit tests for your :class:`intents.Agent` and :class:`intents.Intent` classes can be defined as in any other Python project, testing conversation flows may require simulating **multi-turn interactions** within a session, and check the Agent understanding as the interaction proceeds.

This ``testing`` module provides the following abstractions to facilitate Agent testing through conversational stories:

* :class:`AgentTester` runs in the background and keeps a dev fulfillment service running.
* :class:`TestingStory` wraps a single conversation and models its steps and their assertions.

Setup
=====

Testing frameworks can be configured to automatically instantiate these two objects in the context of a test run. In **pytest** this can be done by defining fixtures in ``conftest.py`` (in the example we use the internal CLI controller to read the Agent configuration from env)

.. code-block:: python

    import pytest

    from intents.cli.agent_controller import AgentController
    from intents.testing import AgentTester

    @pytest.fixture(scope="session")
    def agent_tester() -> AgentTester:
        controller = AgentController.from_env()
        return controller.load_agent_tester()

    @pytest.fixture(scope="function")
    def story(agent_tester):
        return agent_tester.story()

This will instruct *pytest* to inject a :class:`TestingStory` instance in each test function, that can be used to easily assert on single conversation steps:

.. code-block:: python

    def test_order_fish_kipper_followup(story: TestingStory):
        story.step("I want a fish", OrderFish())
        story.step("kipper", OrderFishAnswerKipper())
        story.step("make it three", ChangeAmount(3))

        
Running a test campaign
=======================

An example of this setup can be found in ``/example_agent/test_stories/``. From there, tests can be launched as follows:

#. Spawn a *ngrok* (https://ngrok.com/) process to expose the fulfillment server globally (Dialogflow wil call it as an ``https://...`` endpoint):

   >>> ngrok start 8000

#. Create a ``.env`` configuration from ``.env.template``. Make sure use the same address and port as your *ngrok* tunnel
#. Upload your agent to make sure that the cloud prediction service (e.g. Dialogflow) is aligned with your code.

   >>> dotenv run agentctl upload

#. Wait until the cloud agent completes its training after the upload, and then run the test campaign as any other *pytest* suite:

   >>> poetry shell
   >>> dotenv run pytest -vvv

"""

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

class StaticSentinelMeta(type):
    def __format__(self, fmt):
        return f"<INTENTS:{self.__name__}>"

class StaticSentinel(metaclass=StaticSentinelMeta):

    def __init__(self):
        raise ValueError("Do not instantiate sentinels. Use it like {..., 'foo': IsNone, ...}")

class Anything(StaticSentinel):
    pass

class IsNone(StaticSentinel):
    pass

class IsNotNone(StaticSentinel):
    pass

def _assert_value(value: Any, expected: Any):
    if expected is Anything:
        return
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
    """
    This class models a test conversation, where each step bears the context of the prevous ones, and can define intent assertions.
    
    Each testing story runs in an isolated session, to prevent contexts to alter predictions across different tests.

    Args:
        connector: A Connector object that will be used for predictions
        steps_wait: Waiting time (seconds) in between steps
        session_id: An id for the session. If unset, a random one will be generated as ``intents-test-<UUID>``
    """
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
        """
        Adds a step to the story. This will run the utterance prediction and, if set, perform assertions on the result as well as on its fulfillment call.

        Args:
            utterance_or_step: Typically, this is the message we send to the Agent
            prediction_assert: An assertion on the prediction result. This can simply be the expected Intent; in this case, an assertion will be built to check that the result matches the expectation.
            fulfill_asserts: An utterance may require one or more fulfillment calls to get to the result. These are assertions on the sequence of fulfillment calls.
        """
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
    """
    This is meant to be instantiated at the beginning of a test campaign run.
    
    It will automatically spawn a dev server in the background and will serve as a factory for :class:`TestingStory` objects throughout the campaign. It also checks that the specified connector implements the :class:`intents.connectors.interface.testing.TestableConnector` interface (which is required to make assertions on fulfillment internals)

    Args:
        connector: The connector that will be used to spawn the fulfillment server
        steps_wait: Waiting time (seconds) in between steps
        dev_server: Set to ``false`` if you want to spawn your dev server manually
        dev_server_port: Dev server will run on this port
        dev_server_token: Dev server will check this for authentication
    """

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
        """
        Spawn a background thread running a development fulfillment server with :func:`intents.fulfillment.run_dev_server`.
        """

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
        """
        Returns a :class:`TestingStory` object that is configured to run on the same connector as ``self``.
        """
        return TestingStory(self.connector, self.steps_wait)
