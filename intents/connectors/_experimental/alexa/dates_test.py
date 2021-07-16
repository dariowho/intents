from datetime import date

from intents.connectors._experimental.alexa import dates

def test_specific_date():
    date_from, date_to = dates.parse_alexa_date("2015-11-25")
    assert date_from == date(2015, 11, 25)
    assert date_to is None

def test_specific_week():
    date_from, date_to = dates.parse_alexa_date("2015-W49")
    assert date_from == date(2015, 11, 30)
    assert date_to == date(2015, 12, 6)

def test_weekend():
    date_from, date_to = dates.parse_alexa_date("2015-W49-WE")
    assert date_from == date(2015, 12, 5)
    assert date_to == date(2015, 12, 6)

def test_month_english():
    date_from, date_to = dates.parse_alexa_date("2018-09")
    assert date_from == date(2018, 9, 1)
    assert date_to == date(2018, 9, 30)

    date_from, date_to = dates.parse_alexa_date("2018-01")
    assert date_from == date(2018, 1, 1)
    assert date_to == date(2018, 1, 31)
    
    date_from, date_to = dates.parse_alexa_date("2008-02")
    assert date_from == date(2008, 2, 1)
    assert date_to == date(2008, 2, 29)

    date_from, date_to = dates.parse_alexa_date("2009-02")
    assert date_from == date(2009, 2, 1)
    assert date_to == date(2009, 2, 28)

def test_month_other_languages():
    date_from, date_to = dates.parse_alexa_date("2018-09-XX")
    assert date_from == date(2018, 9, 1)
    assert date_to == date(2018, 9, 30)

    date_from, date_to = dates.parse_alexa_date("2018-01-XX")
    assert date_from == date(2018, 1, 1)
    assert date_to == date(2018, 1, 31)
    
    date_from, date_to = dates.parse_alexa_date("2008-02-XX")
    assert date_from == date(2008, 2, 1)
    assert date_to == date(2008, 2, 29)

    date_from, date_to = dates.parse_alexa_date("2009-02-XX")
    assert date_from == date(2009, 2, 1)
    assert date_to == date(2009, 2, 28)

def test_year_english():
    date_from, date_to = dates.parse_alexa_date("2008")
    assert date_from == date(2008, 1, 1)
    assert date_to == date(2008, 12, 31)

    date_from, date_to = dates.parse_alexa_date("2009")
    assert date_from == date(2009, 1, 1)
    assert date_to == date(2009, 12, 31)

def test_year_other_languages():
    date_from, date_to = dates.parse_alexa_date("2008-XX-XX")
    assert date_from == date(2008, 1, 1)
    assert date_to == date(2008, 12, 31)

    date_from, date_to = dates.parse_alexa_date("2009-XX-XX")
    assert date_from == date(2009, 1, 1)
    assert date_to == date(2009, 12, 31)

def test_decade():
    date_from, date_to = dates.parse_alexa_date("197X")
    assert date_from == date(1970, 1, 1)
    assert date_to == date(1979, 12, 31)

def test_season():
    date_from, date_to = dates.parse_alexa_date("2021-SP")
    assert date_from == date(2021, 3, 21)
    assert date_to == date(2021, 6, 21)

    date_from, date_to = dates.parse_alexa_date("2021-SU")
    assert date_from == date(2021, 6, 22)
    assert date_to == date(2021, 9, 22)

    date_from, date_to = dates.parse_alexa_date("2021-FA")
    assert date_from == date(2021, 9, 23)
    assert date_to == date(2021, 12, 21)

    date_from, date_to = dates.parse_alexa_date("2021-WI")
    assert date_from == date(2021, 12, 22)
    assert date_to == date(2022, 3, 20)
