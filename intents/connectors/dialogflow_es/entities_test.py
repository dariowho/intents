import datetime

from intents import Sys
from intents.connectors.dialogflow_es.entities import TimeEntityMapping, DateEntityMapping, PersonEntityMapping

def test_time_deserialize():
    df_time = "2021-06-19T13:00:00+02:00"
    result = TimeEntityMapping().from_service(df_time)
    expected_tzinfo = datetime.timezone(datetime.timedelta(hours=2))
    assert result == Sys.Time(13, 00, tzinfo=expected_tzinfo)

def test_time_serialize():
    py_time = "11:12:00"
    result = TimeEntityMapping().to_service(py_time)
    assert result == "11:12:00"

    py_time = datetime.time(11, 12)
    result = TimeEntityMapping().to_service(py_time)
    assert result == "11:12:00"

    py_time = Sys.Time(11, 12)
    result = TimeEntityMapping().to_service(py_time)
    assert result == "11:12:00"

def test_date_deserialize():
    df_date = "2021-06-20T12:00:00+02:00"
    result = DateEntityMapping().from_service(df_date)
    assert result == Sys.Date(2021, 6, 20)

def test_date_serialize():
    py_date = "2021-07-21"
    result = DateEntityMapping().to_service(py_date)
    assert result == "2021-07-21"

    py_date = datetime.date(2021, 7, 21)
    result = DateEntityMapping().to_service(py_date)
    assert result == "2021-07-21"

    py_date = Sys.Date(2021, 7, 21)
    result = DateEntityMapping().to_service(py_date)
    assert result == "2021-07-21"

def test_person_deserialize():
    df_person = {
        "name": "John"
    }
    result = PersonEntityMapping().from_service(df_person)
    assert result == Sys.Person("John")

def test_person_serialize():
    py_person = "John"
    result = PersonEntityMapping().to_service(py_person)
    assert result == {"name": "John"}
