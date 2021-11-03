from intents.testing import TestingStory

from example_agent.shop import OrderFish, OrderFishAnswerKipper, OrderKipper, ChangeAmount

def test_order_fish_kipper_followup(story: TestingStory):
    story.step("I want a fish", OrderFish())
    story.step("kipper", OrderFishAnswerKipper())
    story.step("make it three", ChangeAmount(3))

def test_kipper_fallback(story: TestingStory):
    story.step("I'd like to buy a kipper please", OrderKipper())
    story.step("I want to buy 4 kippers", OrderKipper(amount=4))
