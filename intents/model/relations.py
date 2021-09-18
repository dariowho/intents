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
    * It will inherit the parent's **fulfillment** method
    * It will be rendered as a separate, independent intent

      * It will **not** inherit language data such as example utterances and responses

Follow
======

The :func:`follow` relation is a context constraint: an intent that follows another
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
`AskCoffee` starts with a lifespan of 5 (this can be configured by setting a
`lifespan = N` property in the parent Intent class). This value is decremented
at each conversation turn; intents that follow `AskCoffee` can only be predicted
while its lifespan is > 0. :func:`follow` can also replice the current lifespan
of an Intent with a new one (e.g. set it to 0 to kill the context), see its
documentation for details.

It's worth noting that the *follow* relation is **inherited** by subclasses:

* If intent `AskEspresso` is a subclass of `AskCoffee`, and `AddMilk` follows
  `AskCoffe`, then `AddMilk` also follows `AskEspresso`.
* If intent `AskSkimmedMilk` is a subclass of `AskMilk`, and `AskMilk` follows
  `AskCoffee`, then `AskSkimmedMilk` also follows `AskCoffee` (and `AskEspresso`
  in the example above)

API
===
"""
from enum import Enum
from typing import List, Union, Type
import dataclasses
from dataclasses import dataclass, field

from intents import Intent

class RelationType(Enum):
    """
    Currently, the only available type is `RelationType.FOLLOW`. If you want to
    define a *follow* relation, use :func:`follow`.
    """
    FOLLOW = "follow"

@dataclass
class FollowRelationParameters:
    new_lifespan: int
    # fallback: Type[Intent]
    # within: int

def follow(*, new_lifespan: int=None) -> dataclasses.Field:
    """
    This can be used as a value for an Intent Relation field, e.g.

    .. code-block:: python
    
        from intents import follow
        
        @dataclass
        class AddMilk(Intent):
            \"\"\"With milk please\"\"\"
            parent_ask_coffee: AskCoffee = follow()

    This will make "AddMilk" predictable only if AskCoffe was predicted before,
    meaning, it is present in context with lifespan > 0. Lifespan is a counter
    that decreases from a given number (default is 5) at each conversation turn.
    :func:`follow` can update this number, either to keep the context alive, or
    to kill it when it's no more necessary:

    .. code-block:: python

        @dataclass
        class CancelAskCoffee(Intent):
            \"\"\"I don't want coffee anymore...\"\"\"
            parent_ask_coffee: AskCoffee = follow(new_lifespan=0)

    .. warning::

        The returned field currently sets `default=None` as a workaround to some
        known limitations of dataclasses with inheritance. This behavior may be
        adjusted again before 1.0

    Args:
        new_lifespan: Reset the lifespan of the followed intent to the given value
    """
    # TODO: solve inheritance after default fields and remove default
    return field(default=None, metadata={
        "relation_type": RelationType.FOLLOW,
        "relation_parameters": FollowRelationParameters(
            new_lifespan=new_lifespan
        )
    })

@dataclass
class IntentRelation:
    """
    Represent an Intent Relation definition from a "source" Intent (the one that
    defines the relation) to a "target" Intent (the one that is referenced in
    *source*).
    
    For instance, given

    .. code-block:: python

        @dataclass
        class AddMilk(Intent):
            \"\"\"With milk please\"\"\"
            parent_ask_coffee: AskCoffee = follow()

    Then the `follow` relation defined in `AddMilk` can be represented as

    .. code-block:: python

        IntentRelation(
            relation_type=RelationType.FOLLOW
            relation_parameters=None,
            field_name="parent_ask_coffee",
            source_cls=AddMilk,
            target_cls=AskCoffee
        )

    :class:`IntentRelation` objects are typically produced by
    :func:`intent_relations`, and enclosed in its returned
    :class:`IntentRelationMap` result structure.
    
    Args:
        relation_type: One of the relation types
        relation_parameters: Relation parameters as they are specified by the
            relation field
        field_name: Name of the field in `source_cls` that defines the relation
        source_cls: The Intent class where the relation is defined
        target_cls: The other Intent class that is referenced by the relation
    """
    relation_type: RelationType
    relation_parameters: type
    field_name: str
    source_cls: Type[Intent]
    target_cls: Type[Intent]

@dataclass
class FollowIntentRelation(IntentRelation):
    """
    Args:
        relation_parameters: Relation parameters as they are specified by the
            relation field
        field_name: Name of the field in `source_cls` that defines the relation
        source_cls: The Intent class where the relation is defined
        target_cls: The other Intent class that is referenced by the relation
    """
    relation_parameters: FollowRelationParameters
    relation_type: RelationType = field(default=RelationType.FOLLOW, init=None)

@dataclass
class IntentRelationMap:
    """
    A map of an Intent's relations, as it is produced by
    :func:`intent_relations`.

    Args:
        follow: A list of intents that are followed by the Relation subject
    """
    follow: List[FollowIntentRelation] = field(default_factory=list)

def intent_relations(intent: Union[Intent, Type[Intent]]) -> IntentRelationMap:
    """
    Produce a map of all the relations that are defined by the given Intent.

    Args:
        intent: The relation subject. Could be an Intent class or an Intent instance
    """
    intent_cls = intent if isinstance(intent, type) else type(intent)
    result = IntentRelationMap()
    for cls_field in intent.__dataclass_fields__.values():
        relation_type: RelationType = cls_field.metadata.get("relation_type")
        if relation_type:
            assert relation_type in [RelationType.FOLLOW]
            if relation_type == RelationType.FOLLOW:
                # TODO: check that there aren't other equivalent "follow" relations
                # (i.e. with same class or superclasses) in same intent
                relation_parameters: FollowRelationParameters = cls_field.metadata.get("relation_parameters")
                result.follow.append(FollowIntentRelation(
                    relation_parameters=relation_parameters,
                    field_name=cls_field.name,
                    source_cls=intent_cls,
                    target_cls=cls_field.type
                ))

    return result
