"""
This is an example Agent that has a number of Intent categories. Each category
**demonstrates** a specific set of features of the *Intents* library, and
particularly:

* :mod:`~example_agent.smalltalk` shows the **fundamentals** of Intents and their Parameters
* :mod:`~example_agent.shop` demonstrates how to use intent **relations** to control the conversation flow
* :mod:`~example_agent.restaurant` shows how to define **custom entities**
* :mod:`~example_agent.calculator` demonstrates the use of **fulfillments** to include custom logic
  in the Agent's bejavior
* :mod:`~example_agent.travels` demonstrates the use of **rich responses**, such as Images, Cards
  and Quick Replies

.. tip::

    Most of the interesting stuff about the Example Agent comes from its **source code**
    and may not be shown in documentation pages. Hit the `[source]` link (or browse the
    full code at https://github.com/dariowho/intents/tree/master/example_agent/) to know
    more about your topic of interest

  """
from intents import Agent

from example_agent import smalltalk, restaurant, travels, shop, calculator

class ExampleAgent(Agent):
    """
    An example agent that greets its users, and not much more...
    """

ExampleAgent.register(smalltalk)
ExampleAgent.register(restaurant)
ExampleAgent.register(travels)
ExampleAgent.register(shop)
ExampleAgent.register(calculator)
