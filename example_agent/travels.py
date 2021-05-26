"""
The `travels` module demonstrates the use of rich responses, such as images,
cards and quick replies.
"""
from intents import Intent

class user_wants_travel(Intent):
    """
    User: I want to travel
    Agent: How can I help? -> quick replies
    """

class user_ask_hotel_recommendation(Intent):
    """
    User: Recommend me a hotel
    Agent: -hotel card-
    """

class user_ask_holiday_picture(Intent):
    """
    User: Send me a holiday picture
    Agent: -sends picture-
    """
