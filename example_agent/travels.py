"""
The `travels` module demonstrates the use of rich responses, such as images,
cards and quick replies.
"""
from dataclasses import dataclass
from intents import Intent

@dataclass
class UserWantsTravel(Intent):
    """
    | User: I want to travel
    | Agent: How can I help? + **-quick replies-**

    Check out `example_agent/language/en/travels.UserWantsTravel.yaml` for
    language data.
    """

@dataclass
class UserAskHotelRecommendation(Intent):
    """
    | User: Recommend me a hotel
    | Agent: **-hotel card-**

    Check out `example_agent/language/en/travels.UserAskHotelRecommendation.yaml` for
    language data.
    """

@dataclass
class UserAskHolidayPicture(Intent):
    """
    | User: Send me a holiday picture
    | Agent: **-picture-**

    Check out `example_agent/language/en/travels.UserAskHolidayPicture.yaml` for
    language data.
    """

@dataclass
class UserAskTrainStation(Intent):
    """
    | User: Where is the train station?
    | Agent: Address + **-custom payload (location)-**

    Check out `example_agent/language/en/travels.UserAskTrainStation.yaml` for
    language data.
    """
