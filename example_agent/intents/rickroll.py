"""
This module demonstrates the use of Contexts, to condition Agent understanding
on previous conversation history.
"""

from dialogflow_agents import Intent, Context

from example_agent import ExampleAgent

class c_rickroll_started(Context):
    """
    This is spawned when User starts a rickroll
    """

@ExampleAgent.intent('rickroll.user_start')
class user_start(Intent):
    """
    User: "Never gonna"
    Agent: "Give you up"
    """
    meta = Intent.Meta(
        output_contexts=[c_rickroll_started(2)]
    )

@ExampleAgent.intent('rickroll.user_continue')
class user_continue(Intent):
    """
    ...
    User: "Never gonna"
    Agent: "Let you down 🕺"
    """
    meta = Intent.Meta(
        input_contexts=[c_rickroll_started]
    )
