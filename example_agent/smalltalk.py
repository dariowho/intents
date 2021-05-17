"""
These intents demonstrate the fundamentals of a Conversation: Intents,
Entities and Events.
"""
from typing import List
from dataclasses import dataclass

from intents import Intent, Event, Sys

@dataclass
class hello(Intent):
    """
    | User: Hello
    | Agent: Greetings, Human :)

    The **simplest** possible intent: a greetings exchange with no parameters.
    """

@dataclass
class user_name_give(Intent):
    """
    | User: My name is Guido
    | Agent: Hi Guido

    This demonstrates the use of a **system entity** that is recognized in the
    User utterance. Check :mod:`restaurant` for custom entities.
    """
    user_name: Sys.Person

@dataclass
class agent_name_give(Intent):
    """
    | Agent: Howdy Human, my name is $agent_name

    Note that this is Agent sending an unsolicided message to User, rather than
    predicting a response. The language file of the Intent will have no Example
    Utterances, meaning that the Intent can be **triggered**, but will never be
    predicted.
    """
    agent_name: Sys.Person

@dataclass
class user_likes_music(Intent):
    """
    | User: I like music
    | Agent: I love Rock 'n' Roll!

    | User: I like Reggae music
    | Agent: I love Reggae!

    This intent demonstrates the use of **default** parameter values: when User
    doesn't specify a genre, Agent will assume it's Rock 'n' Roll.
    """
    music_genre: Sys.MusicGenre = "Rock 'n' Roll"

@dataclass
class greet_friends(Intent):
    """
    | User: Say hi to my friends Al, John and Jack
    | Agent: Hello Al, John and Jack

    This intent demonstrates the use of **List** parameters. In the example above,
    the `friend_names` parameter will be valued `["Al", "John", "Jack"]`.

    Also, friend_names is a **required** parameter. When User doesn't specify
    names, we want to ask her to do so in a slot filling manner. This is done by
    defining `slot_filling_prompts` in the Intent language file.
    """
    friend_names: List[Sys.Person]

class WelcomeEvent(Event):
    """
    This models an external event that is meant to be sent directly to the
    Agent. It could be a frontend component signaling that the User has just
    opened the chat.
    """

@dataclass
class agent_welcomes_user(Intent):
    events = [WelcomeEvent]

    user_name: Sys.Person
