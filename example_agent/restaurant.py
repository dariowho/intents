"""
This Intents demonstrate the use of **Custom Entities**, which are used to
recognize simple food orders.
"""
from intents import Intent, Entity, Sys
from example_agent import ExampleAgent

class PizzaType(Entity):
    """
    This entity represents different types of pizza, such as Margherita,
    Diavola, etc.
    """

@ExampleAgent.intent("restaurant.order_pizza")
class order_pizza(Intent):
    """
    User is ordering a pizza, like "I want two Margherita please"
    """
    pizza_type: PizzaType
    amount: Sys.Integer = 1
