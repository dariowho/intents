"""
todo:

- support follow()
- render contexts for follow()
- build related intents in prediction
- check cases for DF parameter value
"""
from dataclasses import dataclass

from intents import Intent, Sys, follow

#
# Helpers
#

class CartApi:
    """
    A mock API for a Customer cart. In real life, this connects to a service of
    some sort.
    """
    def add(self, item: str, amount: int):
        print(f"If I was real, I'd add {amount} {item} to cart")

#
# Intents
#

@dataclass
class OrderFish(Intent):
    """
    U: I'd like to buy a fish please
    A: What sort of fish would you like?
    """
    amount: Sys.Integer = 1

    def add_to_cart(self):
        raise NotImplementedError()

@dataclass
class OrderKipper(OrderFish):
    """
    U: I'd like to buy a kipper
    A: Alright, adding 1 kipper to cart
    """

    def add_to_cart(self):
        cart = CartApi()
        cart.add('kipper', self.amount)

@dataclass
class OrderFishAnswerKipper(OrderKipper):
    """
    ("...what sort of fish would you like?")
    U: kipper
    A: Kipper, good choice
    """
    parent_order_fish: OrderFish = follow()
