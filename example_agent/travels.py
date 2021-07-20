"""
The `travels` module demonstrates the use of rich responses, such as images,
cards and quick replies.
"""
from dataclasses import dataclass
from intents import Intent

@dataclass
class user_wants_travel(Intent):
    """
    | User: I want to travel
    | Agent: How can I help? + **-quick replies-**
    """

@dataclass
class user_ask_hotel_recommendation(Intent):
    """
    | User: Recommend me a hotel
    | Agent: **-hotel card-**
    """

@dataclass
class user_ask_holiday_picture(Intent):
    """
    | User: Send me a holiday picture
    | Agent: **-picture-**
    """

@dataclass
class user_ask_train_station(Intent):
    """
    | User: Where is the train station?
    | Agent: Address + **-custom payload (location)-**
    """
