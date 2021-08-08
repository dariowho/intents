"""
These intents demonstrate the fundamentals of a Conversation: Intents and
Entities.
"""
from typing import List
from dataclasses import dataclass

from intents import Intent, Sys

@dataclass
class Hello(Intent):
    """
    | User: Hello
    | Agent: Greetings, Human :)

    The **simplest** possible intent: a greetings exchange with no parameters.
    """

@dataclass
class UserNameGive(Intent):
    """
    | User: My name is Guido
    | Agent: Hi Guido

    This demonstrates the use of a **system entity** that is recognized in the
    User utterance. Check :mod:`example_agent.restaurant` for custom entities.

    Args:
        user_name: User said this is his name
    """
    user_name: Sys.Person

@dataclass
class AgentNameGive(Intent):
    """
    | Agent: Howdy Human, my name is $agent_name

    Note that this is Agent sending an unsolicided message to User, rather than
    predicting a response. The language file of the Intent will have no Example
    Utterances, meaning that the Intent can be **triggered**, but will never be
    predicted.

    Args:
        agent_name: Agent claims this is its name
    """
    agent_name: Sys.Person

@dataclass
class UserLikesMusic(Intent):
    """
    | User: I like music
    | Agent: I love Rock 'n' Roll!

    | User: I like Reggae music
    | Agent: I love Reggae!

    This intent demonstrates the use of **default** parameter values: when User
    doesn't specify a genre, Agent will assume it's Rock 'n' Roll.

    Args:
        music_genre: User said he likes this genre, defaults to "Rock 'n' Roll"
    """
    music_genre: Sys.MusicGenre = "Rock 'n' Roll"

@dataclass
class GreetFriends(Intent):
    """
    | User: Say hi to my friends Al, John and Jack
    | Agent: Hello Al, John and Jack

    This intent demonstrates the use of **List** parameters. In the example above,
    the `friend_names` parameter will be valued `["Al", "John", "Jack"]`.

    Also, friend_names is a **required** parameter. When User doesn't specify
    names, we want to ask her to do so in a slot filling manner. This is done by
    defining `slot_filling_prompts` in the Intent language file.

    Args:
        friend_names: A list of friends to greet
    """
    friend_names: List[Sys.Person]

@dataclass
class UserAsksDay(Intent):
    """
    | User: What day is it?
    | Agent: When?
    | User: today
    | Agent: That would be 2021-06-19

    This is equivalent to :class:`GreetFriends`; they are both intents with a
    required parameter that is prompted to User when missing in the original
    utterance.
    
    One peculiarity of this one is the use of **Sys.Date**: prediction services
    are able to turn spoken time references ("today", "last week", "in a month",
    ...) into absolute values.

    The `date` parameter is automatically casted to a python
    :class:`datetime.date` object when this Intent is predicted
    (:class:`Sys.Date` inherits from :class:`datetime.date`):

    >>> predicted = connector.predict("What day will be tomorrow?")
    >>> predicted.intent.date
    Sys.Date(2021, 6, 20)

    Args:
        date: The date User wants to check
    
    """
    date: Sys.Date
