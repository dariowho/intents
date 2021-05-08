"""
This module demonstrates the use of Contexts, to condition Agent understanding
on previous conversation history.
"""

from intents import Intent, Context

from example_agent import ExampleAgent

class c_rickroll_started(Context):
    """
    This is spawned when User starts a rickroll with :class:`user_start`
    """

@ExampleAgent.intent('rickroll.user_start')
class user_start(Intent):
    """
    | User: "Never gonna"
    | Agent: "Give you up"

    This intent has no input context, but activates :class:`c_rickroll_started`
    with a lifespan of 2 turns.
    """
    meta = Intent.Meta(
        output_contexts=[c_rickroll_started(2)]
    )

@ExampleAgent.intent('rickroll.user_continue')
class user_continue(Intent):
    """
    | User: "Never gonna"
    | Agent: "Let you down 🕺"

    Note that this Intent can only be predicted if :class:`c_rickroll_started`
    is active. Therefore, it can only be predicted after :class:`user_start`.
    """
    meta = Intent.Meta(
        input_contexts=[c_rickroll_started]
    )
