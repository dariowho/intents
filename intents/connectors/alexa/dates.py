"""
The `AMAZON.DATE` slot type in Alexa may return non-standard date formats. Here
we parse them to Python :class:`date` objects. More details at
https://developer.amazon.com/en-US/docs/alexa/custom-skills/slot-type-reference.html#date

.. info::

    Differently from other Services, dates in Alexa can either be specific dates
    (e.g. "2021-07-11") or date intervals (e.g. "2021-W27-WE"). To keep behavior
    consistent we return the first day of the interval. An improvement for the
    future could be to define specific Alexa system entities, to be used in Agents
    that don't need to be compatible with other services.

"""
import re
import calendar
from typing import Tuple, List
from datetime import date, timedelta

SEASONS = {
    "SP": {
        "from": (3, 21),
        "to": (6, 21)
    },
    "SU": {
        "from": (6, 22),
        "to": (9, 22)
    },
    "FA": {
        "from": (9, 23),
        "to": (12, 21)
    },
    "WI": {
        "from": (12, 22),
        "to": (3, 20)
    }
}

def parse_alexa_date(alexa_date: str) -> Tuple[date, date]:
    """
    Parse an Alexa date string, as it is serialized by the `AMAZON.DATE` slot
    type.
    
    Return `date_from` and `date_to` :class:`date` objects. If `alexa_date` is a
    specific date, then `date_to` will be `None`.

    First day of the week is Monday.
    """
    date_from = None
    date_to = None

    # 2015-11-25
    match = re.match(r"^(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})$", alexa_date)
    if match:
        year, month, day = _integer_groups(match, ["year", "month", "day"])
        date_from = date(year, month, day)
        
    # 2015-W49
    match = re.match(r"^(?P<year>\d{4})-W(?P<week>\d{1,2})$", alexa_date)
    if match:
        year, week = _integer_groups(match, ["year", "week"])
        date_from = date.fromisocalendar(year, week, 1)
        date_to = date_from + timedelta(days=6)

    # 2015-W49-WE
    match = re.match(r"^(?P<year>\d{4})-W(?P<week>\d{1,2})-WE$", alexa_date)
    if match:
        year, week = _integer_groups(match, ["year", "week"])
        monday = date.fromisocalendar(year, week, 1)
        date_from = monday + timedelta(days=5)
        date_to = monday + timedelta(days=6)

    # 2018-09 / 2018-09-XX
    match = re.match(r"^(?P<year>\d{4})-(?P<month>\d{1,2})(?:-XX)?$", alexa_date)
    if match:
        year, month = _integer_groups(match, ["year", "month"])
        _, last_day = calendar.monthrange(year, month)
        date_from = date(year, month, 1)
        date_to = date_from.replace(day=last_day)

    # 2018 / 2018-XX-XX
    match = re.match(r"^(?P<year>\d{4})(?:-XX-XX)?$", alexa_date)
    if match:
        year, = _integer_groups(match, ["year"])
        date_from = date(year, 1, 1)
        date_to = date(year, 12, 31)

    # 197X
    match = re.match(r"^(?P<decade>\d{3})X$", alexa_date)
    if match:
        decade, = _integer_groups(match, ["decade"])
        year = decade * 10
        date_from = date(year, 1, 1)
        date_to = date(year+9, 12, 31)

    # 2021-SP / 2021-SU / 2021-FA / 2021-WI
    match = re.match(r"(?P<year>\d{4})-(?P<season>SP|SU|FA|WI)$", alexa_date)
    if match:
        from_year, = _integer_groups(match, ["year"])
        season = match.group("season")
        from_month, from_day = SEASONS[season]["from"]
        to_month, to_day = SEASONS[season]["to"]
        to_year = from_year + 1 if season == "WI" else from_year
        date_from = date(from_year, from_month, from_day)
        date_to = date(to_year, to_month, to_day)

    if date_from:
        return date_from, date_to
    else:
        raise ValueError(f"Could not parse Alexa date string: {alexa_date}. This is possibly a bug, please file an issue at https://github.com/dariowho/intents")

def _integer_groups(match: re.Match, groups=List[str]) -> List[int]:
    result = []
    for g in groups:
        result.append(int(match.group(g)))
    return result
