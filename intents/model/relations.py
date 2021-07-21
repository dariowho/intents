import dataclasses
from typing import List
from dataclasses import dataclass, field, asdict

from intents import Intent

@dataclass
class IntentRelationMetadata:
    relation: str
    field_type: str = 'intent_relation'

def follow():
    # TODO: solve inheritance after default fields and remove default
    return field(default=None, metadata=asdict(IntentRelationMetadata('follow')))
    
@dataclass
class RelatedIntents:
    follow: List[Intent] = field(default_factory=list)

def related_intents(intent: Intent) -> RelatedIntents:
    result = RelatedIntents()
    for field in intent.__dataclass_fields__.values():
        if field.metadata.get("field_type") == "intent_relation":
            relation = field.metadata.get("relation")
            assert relation in ['follow']
            if relation == 'follow':
                result.follow.append(field.type)
    return result
