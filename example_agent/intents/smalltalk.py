from typing import List

from dialogflow_agents import Intent, Event, Sys

from example_agent import ExampleAgent

@ExampleAgent.intent('smalltalk.hello')
class hello(Intent):
    pass

@ExampleAgent.intent('smalltalk.user_name.give')
class user_name_give(Intent):
    user_name: Sys.Person

@ExampleAgent.intent('smalltalk.agent_name.give')
class agent_name_give(Intent):
    agent_name: Sys.Person


@ExampleAgent.intent('smalltalk.greet_friends')
class greet_friends(Intent):
    friend_names: List[Sys.Person]

class WelcomeEvent(Event):
    """
    This models an external event that is meant to be sent directly to the
    Agent. It could be a frontend component signaling that the User has just
    opened the chat.
    """

@ExampleAgent.intent('smalltalk.agent_welcomes_user')
class agent_welcomes_user(Intent):
    meta = Intent.Meta(
        additional_events=[WelcomeEvent]
    )

    user_name: Sys.Person
