"""
This is an example Agent that has a number of Intent categories. Each category
**demonstrates** a specific set of features of the *Intents* library, and
particularly:

* :mod:`smalltalk` shows the fundamentals of Intents and their Parameters
* :mod:`rickroll` demonstrates how to use Context to restrict intent predictions
* :mod:`restaurant` shows how to define Custom Entities

Once the topic of interest is located in the docs, it is advisable to look at
the **source code** of the example Intent definition, to see its implementation
details.
"""

from intents import Agent

from example_agent import smalltalk, rickroll, restaurant

class ExampleAgent(Agent):
    """
    An example agent that greets its users, and not much more...
    """

ExampleAgent.register(smalltalk)
ExampleAgent.register(rickroll)
ExampleAgent.register(restaurant)
