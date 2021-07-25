from dataclasses import dataclass
from intents import Intent
from intents.model.relations import follow, related_intents, RelatedIntents, RelatedIntent, RelationType

def test_related_intents_no_relations():
    
    @dataclass
    class NoRelationsIntent(Intent):
        pass

    result = related_intents(NoRelationsIntent)
    assert isinstance(result, RelatedIntents)
    assert result.follow == []

def test_related_intents_follow():
    
    @dataclass
    class FollowedIntent(Intent):
        pass

    @dataclass
    class FollowingIntent(Intent):
        parent_followed_intent: FollowedIntent = follow()

    result = related_intents(FollowingIntent)
    expected = [
        RelatedIntent(
            field_name='parent_followed_intent',
            relation_type=RelationType.FOLLOW,
            intent_cls=FollowedIntent
        )
    ]
    assert result.follow == expected

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

    result = related_intents(FollowingIntentSubclass)
    expected = [
        RelatedIntent(
            field_name='parent_followed_intent',
            relation_type=RelationType.FOLLOW,
            intent_cls=FollowedIntent
        )
    ]
    assert result.follow == expected
