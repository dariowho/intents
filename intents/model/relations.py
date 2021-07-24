"""
The interpretation of an utterance may change depending on the context of the
conversation. Context-dependant dynamics in the conversation are modeled by the
**relations** intents have with each other. This module defines an API to
specify them.

.. warning::

   Relations are currently undocumented. Please refer to the
   :mod:`example_agent.shop` example instead.
"""

import dataclasses
from enum import Enum
from typing import List
from dataclasses import dataclass, field, asdict

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
