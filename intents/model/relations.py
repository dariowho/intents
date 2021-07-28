"""
The interpretation of an utterance may change depending on the context of the
conversation. Context-dependant dynamics in the conversation are modeled by the
**relations** intents have with each other. This module defines an API to
specify them.

.. note::

   Usage of relations is demonstrated in the :mod:`example_agent.shop` module of
   the Example Agent

Inheritance
===========
Since we define intents as Python classes, we can reuse of one of the founding
concepts of object oriented programming: **inheritance**.

.. code-block:: python

    @dataclass
    class AskCoffee(Intent):
        \"\"\"Hello, I'd like a light roast coffee\"\"\"
        roast_level: CoffeeRoastLevel = "medium"

    @dataclass
    class AskEspresso(AskCoffee):
        \"\"\"Hello, I'd like a dark roast espresso.\"\"\"

An intent should subclass another when its meaning **includes and specifies**
the meaning of the other intent. When an intent is a subclass of another:

    * It will inherit all **parameters**, types and default values of the parent intent
    * It will inherit all the other **relations** of the parent intent
    * It will be rendered as a separate, independent intent

      * It will **not** inherit language data such as example utterances and responses

Follow
======

The **follow** relation is a context constraint: an intent that follows another
one can only be predicted after the followed one.

.. code-block:: python

    from intents import follow

    @dataclass
    class AddMilk(Intent):
        \"\"\"With milk please\"\"\"
        parent_ask_coffee: AskCoffee = follow()

An intent should follow another when it only makes sense in the parent's
context. In the example, it doesn't make sense to walk into a cafè and utter
"With milk please"; however, it does make sense to say so after asking for a
coffee.

Context parameters can be accessed with another OOP fundamental concept:
**composition**.

.. code-block:: python

    >>> prediction = connector.predict("I want a dark roast espresso")
    >>> prediction = connector.predict("With milk please")
    >>> prediction.intent.parent_ask_coffee.roast_level
    "dark"

This relation is implemented by looking at the **lifespan** of intents.
`AskCoffee` starts with a lifespan of 5 (at the moment this is constant and
can't be configured). This value is decremented at each conversation turn;
intents that follow `AskCoffee` can only be predicted while its lifespan is > 0.

It's worth noting that the *follow* relation is **inherited** by subclasses:

* If intent `AskEspresso` is a subclass of `AskCoffee`, and `AddMilk` follows
  `AskCoffe`, then `AddMilk` also follows `AskEspresso`.
* If intent `AskSkimmedMilk` is a subclass of `AskMilk`, and `AskMilk` follows
  `AskCoffee`, then `AskSkimmedMilk` also follows `AskCoffee` (and `AskEspresso`
  in the example above)
"""
from enum import Enum
from typing import List
from dataclasses import dataclass, field

from intents import Intent
from intents.model.intent import _IntentMetaclass

class RelationType(Enum):
    FOLLOW = "follow"

@dataclass
class IntentRelationMetadata:
    relation: str
    field_type: str = 'intent_relation'

def follow():
    # TODO: solve inheritance after default fields and remove default
    return field(default=None, metadata={"relation_type": RelationType.FOLLOW})
    # return field(default=None, metadata=asdict(IntentRelationMetadata('follow')))

@dataclass
class RelatedIntent:
    field_name: str
    relation_type: RelationType
    intent_cls: _IntentMetaclass

@dataclass
class RelatedIntents:
    follow: List[RelatedIntent] = field(default_factory=list)

def related_intents(intent: Intent) -> RelatedIntents:
    result = RelatedIntents()
    for cls_field in intent.__dataclass_fields__.values():
        relation_type: RelationType = cls_field.metadata.get("relation_type")
        if relation_type:
            assert relation_type in [RelationType.FOLLOW]
            if relation_type == RelationType.FOLLOW:
                result.follow.append(RelatedIntent(
                    field_name=cls_field.name,
                    relation_type=relation_type,
                    intent_cls=cls_field.type
                ))

    return result
