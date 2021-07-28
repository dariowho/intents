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
    """

@dataclass
class OrderPizza(Intent):
    """
    User is ordering a pizza, like "I want two Margherita please"
    """
    pizza_type: PizzaType
    amount: Sys.Integer = 1
