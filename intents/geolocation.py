from dataclasses import dataclass

@dataclass
class Location:
    lat: float
    lng: float
    formatted_address: str = None
    zip_code: str = None
    city: str = None

