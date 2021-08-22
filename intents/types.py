"""
In *Intents*, Agent components are defined as Python classes. This means that in
your Agent project you are likely to deal with Intent/Entity **classes**, as
well as with their **instances**.

Annotating types in your code is trivial for class instances, for example:

.. code-block:: python

    @dataclass
    class OrderPizzaIntent(Intent):
        pizza_type: PizzaType = "margherita"

    def make_pizza_order(predicted_intent: OrderPizzaIntent):
        api.order_pizza(type=predicted_intent.pizza_type)

However, it is not as convenient to do the same for classes:

.. code-block:: python

    def print_intent_definition(intent_cls: type):
        print(intent_cls.parameter_schema)

The annotation above doesn't tell us much about `intent_cls`. To make typing
annotation easier and more meaningful, here we collect the **metaclasses** that
are used to define :class:`~intents.model.agent.Agent`,
:class:`~intents.model.intent.Intent` and :class:`~intents.model.entity.Entity`.

We call them **types**, and can be used to annotate parameters that reference an
Intent or Entity class, instead of their instances.

.. code-block:: python

    from intents.types import IntentType

    def print_intent_definition(intent_cls: IntentType):
        print(intent_cls.parameter_schema)
"""
# pylint: disable=unused-import
from intents.model.agent import AgentType
from intents.model.intent import IntentType
from intents.model.entity import EntityType
