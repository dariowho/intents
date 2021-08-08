from intents.connectors._experimental.snips import prediction_format as pf

def test_from_dict_no_slots():
    parse_result = {
        'input': 'I want a coffee',
        'intent': {'intentName': 'AskCoffee', 'probability': 0.65},
        'slots': []
    }
    expected = pf.ParseResult(
        input="I want a coffee",
        intent=pf.ParseResultIntent(
            intentName="AskCoffee",
            probability=0.65
        ),
        slots=[]
    )
    assert pf.from_dict(parse_result) == expected

def test_from_dict_slots():
    parse_result = {
        'input': 'I want a dark roast espresso',
        'intent': {'intentName': 'AskEspresso', 'probability': 0.56},
        'slots': [
            {
                'range': {'start': 9, 'end': 13},
                'rawValue': 'dark',
                'value': {'kind': 'Custom', 'value': 'dark'},
                'entity': 'CoffeeRoast',
                'slotName': 'roast'
            }
        ]
    }
    expected = pf.ParseResult(
        input="I want a dark roast espresso",
        intent=pf.ParseResultIntent(
            intentName="AskEspresso",
            probability=0.56
        ),
        slots=[
            pf.ParseResultSlot(
                range=pf.ParseResultSlotRange(start=9, end=13),
                rawValue="dark",
                value={'kind': 'Custom', 'value': 'dark'},
                entity="CoffeeRoast",
                slotName="roast"
            )
        ]
    )
    assert pf.from_dict(parse_result) == expected
