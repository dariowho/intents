from dataclasses import dataclass
from typing import List, Optional
import dacite

@dataclass
class ParseResultIntent:
    intentName: Optional[str] = None # None when no intent is predicted
    probability: Optional[float] = None

@dataclass
class ParseResultSlotRange:
    start: int
    end: int

@dataclass
class ParseResultSlot:
    range: ParseResultSlotRange
    rawValue: str
    value: dict
    entity: str
    slotName: str

@dataclass
class ParseResult:
    input: str
    intent: ParseResultIntent
    slots: List[ParseResultSlot]

def from_dict(parse_result: dict):
    # TODO: handle fallback (intentName=None)
    return dacite.from_dict(ParseResult, parse_result)
