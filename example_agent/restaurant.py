"""
This Intents demonstrate the use of **Custom Entities**, which are used to
recognize simple food orders.
"""
from dataclasses import dataclass

from intents import Intent, Entity, Sys

class PizzaType(Entity):
    """
    This entity represents different types of pizza, such as Margherita,
    Diavola, etc.

    Language data for this entity can be found in
    `example_agent/language/en/ENTITY_PizzaType.yaml`.
    """

@dataclass
class OrderPizza(Intent):
    """
    User is ordering a pizza, like "I want two Margherita please"

    Args:
        pizza_type: The type of pizza User wants to order
        amount: The amount of pizzas User wants to order
    """
    pizza_type: PizzaType
    amount: Sys.Integer = 1
