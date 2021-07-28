"""
This module demonstrates the use of Contexts, to condition Agent understanding
on previous conversation history.

.. warning::

    Contexts are **deprecated** and will be removed in 0.3. Upgrade your code to use 
    :mod:`intents.model.relations` instead.
"""
from dataclasses import dataclass

from intents import Intent, Context

class c_rickroll_started(Context):
    """
    This is spawned when User starts a rickroll with :class:`user_start`
    """

@dataclass
class user_start(Intent):
    """
    | User: "Never gonna"
    | Agent: "Give you up"

    This intent has no input context, but activates :class:`c_rickroll_started`
    with a lifespan of 2 turns.
    """
    output_contexts = [c_rickroll_started(2)]

@dataclass
class user_continue(Intent):
    """
    | User: "Never gonna"
    | Agent: "Let you down 🕺"

    Note that this Intent can only be predicted if :class:`c_rickroll_started`
    is active. Therefore, it can only be predicted after :class:`user_start`.
    """
    input_contexts = [c_rickroll_started]
