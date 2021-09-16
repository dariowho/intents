from dataclasses import dataclass
from intents import Intent
from intents.model.relations import follow, intent_relations, IntentRelationMap, IntentRelation, RelationType, FollowRelationParameters, FollowIntentRelation

def test_intent_relations__no_relations():
    
    @dataclass
    class NoRelationsIntent(Intent):
        pass

    result = intent_relations(NoRelationsIntent)
    assert isinstance(result, IntentRelationMap)
    assert result.follow == []

def test_intent_relations__follow():
    
    @dataclass
    class FollowedIntent(Intent):
        pass

    @dataclass
    class FollowingIntent(Intent):
        parent_followed_intent: FollowedIntent = follow()

    result = intent_relations(FollowingIntent)
    expected = [
        FollowIntentRelation(
            relation_parameters=FollowRelationParameters(new_lifespan=None),
            field_name='parent_followed_intent',
            source_cls=FollowingIntent,
            target_cls=FollowedIntent
        )
    ]
    assert result.follow == expected
    assert result.follow[0].relation_type == RelationType.FOLLOW

def test_subclass_inherits_follow():

    @dataclass
    class FollowedIntent(Intent):
        pass

    @dataclass
    class FollowingIntent(Intent):
        parent_followed_intent: FollowedIntent = follow()

    @dataclass
    class FollowingIntentSubclass(FollowingIntent):
        pass

    result = intent_relations(FollowingIntentSubclass)
    expected = [
        FollowIntentRelation(
            relation_parameters=FollowRelationParameters(new_lifespan=None),
            field_name='parent_followed_intent',
            source_cls=FollowingIntentSubclass,
            target_cls=FollowedIntent
        )
    ]
    assert result.follow == expected
    assert result.follow[0].relation_type == RelationType.FOLLOW
