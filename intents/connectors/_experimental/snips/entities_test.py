from datetime import datetime

import pytest

from intents import Sys
from intents.connectors._experimental.snips import entities
from intents.connectors._experimental.snips import prediction_format as pf

def test_date_mapping_from_service():
    mapping = entities.DateMapping()
    snips_date_result = {
        'input': 'My birthday is on august 24',
        'intent': {
            'intentName': 'UserSaysBirthday',
            'probability': 1.0
        },
        'slots': [
            {
                'range': {'start': 15, 'end': 27},
                'rawValue': 'on august 24',
                'value': {
                    'kind': 'InstantTime',
                    'value': '2021-08-24 00:00:00 +02:00',
                    'grain': 'Day',
                    'precision': 'Exact'
                },
                'entity': 'snips/date',
                'slotName': 'birthday_date'
            }
        ]
    }
    parse_result = pf.from_dict(snips_date_result)
    entity = mapping.from_service(parse_result.slots[0].value)
    assert entity == Sys.Date(2021, 8, 24)

def test_date_mapping_unexpected_grain():
    mapping = entities.DateMapping()
    value = {
        'kind': 'InstantTime',
        'value': '2021-08-24 00:00:00 +02:00',
        'grain': 'Month',
        'precision': 'Exact'
    }
    entity = mapping.from_service(value)
    with pytest.warns(None):
        assert entity == Sys.Date(2021, 8, 24)

def test_date_mapping_unexpected_kind():
    mapping = entities.DateMapping()
    value = {
        'kind': 'UNEXPECTED',
        'value': '2021-08-24 00:00:00 +02:00',
        'grain': 'Day',
        'precision': 'Exact'
    }
    entity = mapping.from_service(value)
    with pytest.warns(None):
        assert entity == Sys.Date(2021, 8, 24)

def test_date_mapping_to_service():
    mapping = entities.DateMapping()
    assert mapping.to_service(Sys.Date(2021, 8, 8)) == "2021-08-08"
    assert mapping.to_service(datetime(year=2021, month=8, day=8)) == "2021-08-08"
