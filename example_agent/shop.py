"""
This module demonstrates the use of intent **relations** to create complex
conversation flows.

.. note::

    Intent relations are under definition, they will be extended in next releases.

Let's break down a complex interaction involving :mod:`shop` intents.

#. 
   .. code-block:: text

       U: I want a fish
       A: What sort of fish do you want?

   Standard Intent :class:`OrderFish` starts the conversation.

   .. autoclass:: OrderFish

#. 
   .. code-block:: text

       U: A kipper
       A: Kipper, good choice. Adding 1 to cart

   Intent :class:`OrderFishAnswerKipper` follows :class:`OrderFish`. This means
   that the first can't be predicted if the latter wasn't predicted recently;
   this makes sense because an utterance like *"a kipper"* would sound really
   weird without context. Note that :class:`OrderFishAnswerKipper` is a subclass
   of :class:`OrderKipper`, and therefore inherits its
   :meth:`OrderKipper.fulfill` method.

   Check out the **source code** of the intents below to see how the *follow*
   relation is implemented.

   .. autoclass:: OrderKipper
      :members:

   .. autoclass:: OrderFishAnswerKipper
      :members:


#. 
   .. code-block:: text

       U: Actually I want more
       A: How many would you like?

   :class:`ChangeAmount` follows :class:`OrderKipper`. Since
   :class:`OrderFishAnswerKipper` is a subclass of :class:`OrderKipper`, our
   agent can predict :class:`ChangeAmount` at this point of the conversation.
   However, this intent defines a required parameter
   :attr:`ChangeAmount.amount`. Since *amount* can't be tagged in the user
   utterance, the Agent will respond with one of the slot filling prompts for
   parameter "amount" (see :mod:`intents.language`).

   .. autoclass:: ChangeAmount
      :members:

#. 
   .. code-block:: text

       U: 3 please
       A: Alright, I changed the amount to 3

   User fills the slot, and :class:`ChangeAmount` can finally be predicted.

.. autoclass:: CartApi
    :members:
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
        """
        Add an item to cart
        
        Args:
            item: Name of the item to add
            amount: Amount to add
        """
        print(f"If I was real, I'd add {amount} {item} to cart")

    def update(self, item: str, amount: int):
        """
        Update an item in cart
        
        Args:
            item: Name of the item to update
            amount: New amount to set
        """
        print(f"If I was real, I'd update the amount of {item} to {amount}")

#
# Intents
#

@dataclass
class OrderFish(Intent):
    """
    | U: I'd like to buy a fish please
    | A: What sort of fish would you like?

    Args:
        amount: The amount of fish to buy
    """
    lifespan = 3

    amount: Sys.Integer = 1

@dataclass
class OrderKipper(OrderFish):
    """
    | U: I'd like to buy a kipper
    | A: Alright, adding 1 kipper to cart

    Args:
        amount: The amount of kipper to buy
    """

    def fulfill(self, context, *args):
        """
        Use :class:`CartApi` to add kippers to cart. The amount is specified by
        :attr:`OrderKipper.amount`
        """
        cart = CartApi()
        cart.add('kipper', self.amount)

@dataclass
class OrderFishAnswerKipper(OrderKipper):
    """
    | ("...what sort of fish would you like?")
    | U: kipper
    | A: Kipper, good choice

    Args:
        amount: The amount of kipper to buy
        parent_order_fish: The OrderFish intent from context
    """
    parent_order_fish: OrderFish = follow()

@dataclass
class ChangeAmount(Intent):
    """
    | ("...adding one kipper to cart")
    | U: actually, make it 2
    | A: Sure, 2 kippers for you

    Args:
        amount: The new amount of kipper. Note that this overwrites all the
            other values for parameter "amount" in context, even if they come from
            other intents
        parent_order_kipper: The OrderKipper intent from context
    """
    amount: Sys.Integer

    parent_order_kipper: OrderKipper = follow(new_lifespan=2)

    def fulfill(self, context, *args):
        """
        Use :class:`CartApi` to update the amount of kippers in cart to :attr:`ChangeAmount.amount`
        """
        cart = CartApi()
        cart.update('kipper', self.amount)
