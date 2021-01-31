from dialogflow_agents import Intent

from example_agent import ExampleAgent

@ExampleAgent.intent('smalltalk.hello')
class hello(Intent):
    pass

@ExampleAgent.intent('smalltalk.user_name.give')
class user_name_give(Intent):
    user_name: str

@ExampleAgent.intent('smalltalk.agent_name.give')
class agent_name_give(Intent):
    agent_name: str
