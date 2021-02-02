from dialogflow_agents import Intent
from dialogflow_agents.system_entities import sys

from example_agent import ExampleAgent

@ExampleAgent.intent('smalltalk.hello')
class hello(Intent):
    pass

@ExampleAgent.intent('smalltalk.user_name.give')
class user_name_give(Intent):
    user_name: sys.person()

@ExampleAgent.intent('smalltalk.agent_name.give')
class agent_name_give(Intent):
    agent_name: sys.person()
