import json
from unittest.mock import patch
from typing import List
from dataclasses import dataclass

import pytest

from intents import Intent, Entity, Agent, LanguageCode, Sys
from intents.language import EntityEntry
from intents.connectors._experimental.alexa import fulfillment, fulfillment_schemas, names, language

BASE_FULFILLMENT_BODY = json.loads("""{
    "version": "1.0",
    "session": {
        "new": false,
        "sessionId": "amzn1.echo-api.session.fake-session-id",
        "application": {
            "applicationId": "amzn1.ask.skill.fake-application-id"
        },
        "user": {
            "userId": "amzn1.ask.account.fake-user-id"
        }
    },
    "context": {
        "Viewports": [
            {
                "type": "APL",
                "id": "main",
                "shape": "RECTANGLE",
                "dpi": 213,
                "presentationType": "STANDARD",
                "canRotate": false,
                "configuration": {
                    "current": {
                        "mode": "HUB",
                        "video": {
                            "codecs": [
                                "H_264_42",
                                "H_264_41"
                            ]
                        },
                        "size": {
                            "type": "DISCRETE",
                            "pixelWidth": 1280,
                            "pixelHeight": 800
                        }
                    }
                }
            }
        ],
        "Viewport": {
            "experiences": [
                {
                    "arcMinuteWidth": 346,
                    "arcMinuteHeight": 216,
                    "canRotate": false,
                    "canResize": false
                }
            ],
            "mode": "HUB",
            "shape": "RECTANGLE",
            "pixelWidth": 1280,
            "pixelHeight": 800,
            "dpi": 213,
            "currentPixelWidth": 1280,
            "currentPixelHeight": 800,
            "touch": [
                "SINGLE"
            ],
            "video": {
                "codecs": [
                    "H_264_42",
                    "H_264_41"
                ]
            }
        },
        "Extensions": {
            "available": {
                "aplext:backstack:10": {}
            }
        },
        "System": {
            "application": {
                "applicationId": "amzn1.ask.skill.fake-application-id"
            },
            "user": {
                "userId": "amzn1.ask.account.fake-user-id"
            },
            "device": {
                "deviceId": "amzn1.ask.device.fake-device-id",
                "supportedInterfaces": {
                    "Alexa.Presentation.APL": {
                        "runtime": {
                            "maxVersion": "1.7"
                        }
                    }
                }
            },
            "apiEndpoint": "https://api.amazonalexa.com",
            "apiAccessToken": "aaA0aAAaAaAAA0AaAAAaaAaaAaAAAaA0AaAaAaaaAAA0AaAaaA.fake-access-token"
        }
    },
    "request": {}
}""")

class MockExampleAgent(Agent):
    """
    Real example agent may change
    """
    languages = ["en", "it"]

@dataclass
class ToyIntent(Intent):
    name = "ToyIntent"

class MockPizzaType(Entity):
    name="PizzaType"
    __entity_language_data__ = {
        LanguageCode.ENGLISH: [
            EntityEntry("Margherita", []),
            EntityEntry("Diavola", ['pepperoni']),
        ],
        LanguageCode.ITALIAN: [
            EntityEntry("Margherita", []),
            EntityEntry("Diavola", ['salamino piccante']),
        ]
    }

@dataclass
class MockOrderPizza(Intent):
    name = "restaurant.OrderPizza"

    pizza_type: MockPizzaType
    amount: Sys.Integer = 1

class MockCalculatorOperator(Entity):
    name="CalculatorOperator"

    __entity_language_data__ = {
        LanguageCode.ENGLISH: [
            EntityEntry("*", ["multiplied by", "times"]),
            EntityEntry("-", ['minus']),
        ],
        LanguageCode.ITALIAN: [
            EntityEntry("*", ["per", "moltiplicato"]),
            EntityEntry("-", ['meno']),
        ]
    }

@dataclass
class MockSolveMathOperation(Intent):
    name = "calculator.SolveMathOperation"

    first_operand: Sys.Integer
    second_operand: Sys.Integer
    operator: MockCalculatorOperator

@dataclass
class MockGreetFriends(Intent):
    name = "smalltalk.GreetFriends"

    friend_names: List[Sys.Person]

with patch('intents.language.intent_language_data'):
    MockExampleAgent.register(MockOrderPizza)
    MockExampleAgent.register(MockSolveMathOperation)
    MockExampleAgent.register(MockGreetFriends)
    MockExampleAgent.register(ToyIntent)

def _build_fulfillment_body_dict(request_dict: dict) -> dict:
    result = BASE_FULFILLMENT_BODY.copy()
    result["request"] = request_dict
    return result

def _get_fulfillment_component():
    names_component = names.AlexaNamesComponent(MockExampleAgent)
    language_component = language.AlexaLanguageComponent(MockExampleAgent)
    return fulfillment.AlexaFulfillmentComponent(
        MockExampleAgent,
        names_component,
        language_component
    )

def test_build_intent_single_parameter():
    # OrderPizza(pizza_type="Margherita")
    ORDER_PIZZA_REQUEST = json.loads("""{
            "type": "IntentRequest",
            "requestId": "amzn1.echo-api.request.45f9da6f-f39b-41b4-b5fd-46d0cbf875cd",
            "locale": "en-US",
            "timestamp": "2021-08-12T20:02:52Z",
            "intent": {
                "name": "restaurant_OrderPizza",
                "confirmationStatus": "NONE",
                "slots": {
                    "amount": {
                        "name": "amount",
                        "confirmationStatus": "NONE"
                    },
                    "pizza_type": {
                        "name": "pizza_type",
                        "value": "margherita",
                        "resolutions": {
                            "resolutionsPerAuthority": [
                                {
                                    "authority": "amzn1.er-authority.echo-sdk.amzn1.ask.skill.fake-application-id.PizzaType",
                                    "status": {
                                        "code": "ER_SUCCESS_MATCH"
                                    },
                                    "values": [
                                        {
                                            "value": {
                                                "name": "Margherita",
                                                "id": "PizzaType-Margherita"
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        "confirmationStatus": "NONE",
                        "source": "USER",
                        "slotValue": {
                            "type": "Simple",
                            "value": "margherita",
                            "resolutions": {
                                "resolutionsPerAuthority": [
                                    {
                                        "authority": "amzn1.er-authority.echo-sdk.amzn1.ask.skill.fake-application-id.PizzaType",
                                        "status": {
                                            "code": "ER_SUCCESS_MATCH"
                                        },
                                        "values": [
                                            {
                                                "value": {
                                                    "name": "Margherita",
                                                    "id": "PizzaType-Margherita"
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
    """)
    fulfillment_component = _get_fulfillment_component()

    fulfillment_body_dict = _build_fulfillment_body_dict(ORDER_PIZZA_REQUEST)
    body = fulfillment_schemas.from_dict(fulfillment_body_dict)
    intent = fulfillment_component.intent_from_fulfillment(body, lang=LanguageCode.ENGLISH)

    assert intent == MockOrderPizza(pizza_type="Margherita")

def test_build_intent_normalizes_entity_values():
    # SolveMathOperation(first_operand=4, second_operand=5, operator="*")
    #                                                                 ^ must be normalized
    CALCULATOR_REQUEST = json.loads("""{
            "type": "IntentRequest",
            "requestId": "amzn1.echo-api.request.077b28ef-9c2b-4373-a250-d70d5b90a0bd",
            "locale": "en-US",
            "timestamp": "2021-08-12T20:07:38Z",
            "intent": {
                "name": "calculator_SolveMathOperation",
                "confirmationStatus": "NONE",
                "slots": {
                    "first_operand": {
                        "name": "first_operand",
                        "value": "4",
                        "confirmationStatus": "NONE",
                        "source": "USER",
                        "slotValue": {
                            "type": "Simple",
                            "value": "4"
                        }
                    },
                    "second_operand": {
                        "name": "second_operand",
                        "value": "5",
                        "confirmationStatus": "NONE",
                        "source": "USER",
                        "slotValue": {
                            "type": "Simple",
                            "value": "5"
                        }
                    },
                    "operator": {
                        "name": "operator",
                        "value": "times",
                        "resolutions": {
                            "resolutionsPerAuthority": [
                                {
                                    "authority": "amzn1.er-authority.echo-sdk.amzn1.ask.skill.fake-application-id.CalculatorOperator",
                                    "status": {
                                        "code": "ER_SUCCESS_MATCH"
                                    },
                                    "values": [
                                        {
                                            "value": {
                                                "name": "multiplied by",
                                                "id": "CalculatorOperator-multipliedby"
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        "confirmationStatus": "NONE",
                        "source": "USER",
                        "slotValue": {
                            "type": "Simple",
                            "value": "times",
                            "resolutions": {
                                "resolutionsPerAuthority": [
                                    {
                                        "authority": "amzn1.er-authority.echo-sdk.amzn1.ask.skill.fake-application-id.CalculatorOperator",
                                        "status": {
                                            "code": "ER_SUCCESS_MATCH"
                                        },
                                        "values": [
                                            {
                                                "value": {
                                                    "name": "multiplied by",
                                                    "id": "CalculatorOperator-multipliedby"
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }"""
    )
    fulfillment_component = _get_fulfillment_component()

    fulfillment_body_dict = _build_fulfillment_body_dict(CALCULATOR_REQUEST)
    body = fulfillment_schemas.from_dict(fulfillment_body_dict)
    intent = fulfillment_component.intent_from_fulfillment(body, lang=LanguageCode.ENGLISH)

    assert intent == MockSolveMathOperation(first_operand=4, second_operand=5, operator="*")

def test_list_slot_single_value():

    # Greet friends with a single friend
    LIST_SLOT_REQUEST__SINGLE_VALUE = json.loads("""{
        "type": "IntentRequest",
        "requestId": "amzn1.echo-api.request.fake-api-request",
        "locale": "en-US",
        "timestamp": "2021-08-11T21:46:11Z",
        "intent": {
            "name": "smalltalk_GreetFriends",
            "confirmationStatus": "NONE",
            "slots": {
                "friend_names": {
                    "name": "friend_names",
                    "value": "John",
                    "resolutions": {
                        "resolutionsPerAuthority": [
                            {
                                "authority": "AlexaEntities",
                                "status": {
                                    "code": "ER_SUCCESS_MATCH"
                                },
                                "values": [
                                    {
                                        "value": {
                                            "name": "John",
                                            "id": "https://ld.amazonalexa.com/entities/v1/1NaUgygHJx0BHxfQcKICqn"
                                        }
                                    },
                                    {
                                        "value": {
                                            "name": "John",
                                            "id": "https://ld.amazonalexa.com/entities/v1/5MPA8cqc69MBzaK3Z91KU9"
                                        }
                                    },
                                    {
                                        "value": {
                                            "name": "John",
                                            "id": "https://ld.amazonalexa.com/entities/v1/B2ebljbbk5pDAFEnHBPBXV"
                                        }
                                    },
                                    {
                                        "value": {
                                            "name": "John",
                                            "id": "https://ld.amazonalexa.com/entities/v1/HFaP3f1ENFoFfLQTbsC989"
                                        }
                                    },
                                    {
                                        "value": {
                                            "name": "John",
                                            "id": "https://ld.amazonalexa.com/entities/v1/uU6qXLKVIG9gK9jax0Lj00"
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    "confirmationStatus": "NONE",
                    "source": "USER",
                    "slotValue": {
                        "type": "Simple",
                        "value": "John",
                        "resolutions": {
                            "resolutionsPerAuthority": [
                                {
                                    "authority": "AlexaEntities",
                                    "status": {
                                        "code": "ER_SUCCESS_MATCH"
                                    },
                                    "values": [
                                        {
                                            "value": {
                                                "name": "John",
                                                "id": "https://ld.amazonalexa.com/entities/v1/1NaUgygHJx0BHxfQcKICqn"
                                            }
                                        },
                                        {
                                            "value": {
                                                "name": "John",
                                                "id": "https://ld.amazonalexa.com/entities/v1/5MPA8cqc69MBzaK3Z91KU9"
                                            }
                                        },
                                        {
                                            "value": {
                                                "name": "John",
                                                "id": "https://ld.amazonalexa.com/entities/v1/B2ebljbbk5pDAFEnHBPBXV"
                                            }
                                        },
                                        {
                                            "value": {
                                                "name": "John",
                                                "id": "https://ld.amazonalexa.com/entities/v1/HFaP3f1ENFoFfLQTbsC989"
                                            }
                                        },
                                        {
                                            "value": {
                                                "name": "John",
                                                "id": "https://ld.amazonalexa.com/entities/v1/uU6qXLKVIG9gK9jax0Lj00"
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                },
                "__Conjunction": {
                    "name": "__Conjunction",
                    "confirmationStatus": "NONE"
                }
            }
        }
    }""")
    fulfillment_component = _get_fulfillment_component()

    fulfillment_body_dict = _build_fulfillment_body_dict(LIST_SLOT_REQUEST__SINGLE_VALUE)
    body = fulfillment_schemas.from_dict(fulfillment_body_dict)
    with pytest.warns(None):
        intent = fulfillment_component.intent_from_fulfillment(body, lang=LanguageCode.ENGLISH)

    assert intent == MockGreetFriends(friend_names=["John"])

def test_list_slot_list_value():

    LIST_SLOT_REQUEST__LIST_VALUE = json.loads("""{
        "type": "IntentRequest",
        "requestId": "amzn1.echo-api.request.258ed402-09b7-46f1-82e0-b01102829aa3",
        "locale": "en-US",
        "timestamp": "2021-08-11T21:58:24Z",
        "intent": {
            "name": "smalltalk_GreetFriends",
            "confirmationStatus": "NONE",
            "slots": {
                "friend_names": {
                    "name": "friend_names",
                    "confirmationStatus": "NONE",
                    "source": "USER",
                    "slotValue": {
                        "type": "List",
                        "values": [
                            {
                                "type": "Simple",
                                "value": "Al John",
                                "resolutions": {
                                    "resolutionsPerAuthority": [
                                        {
                                            "authority": "AlexaEntities",
                                            "status": {
                                                "code": "ER_SUCCESS_MATCH"
                                            },
                                            "values": [
                                                {
                                                    "value": {
                                                        "name": "Al St. John",
                                                        "id": "https://ld.amazonalexa.com/entities/v1/1684nfEDrbFDPS5zG3J9Xh"
                                                    }
                                                },
                                                {
                                                    "value": {
                                                        "name": "Al. John",
                                                        "id": "https://ld.amazonalexa.com/entities/v1/15clLtXk5V8G1eOUXS7e6U"
                                                    }
                                                },
                                                {
                                                    "value": {
                                                        "name": "Con Covert",
                                                        "id": "https://ld.amazonalexa.com/entities/v1/FQThPE13ILbFNfD9kAkQSA"
                                                    }
                                                },
                                                {
                                                    "value": {
                                                        "name": "Kenny Clarke",
                                                        "id": "https://ld.amazonalexa.com/entities/v1/2VrKlUBYfd4CCfrQaYXwhe"
                                                    }
                                                },
                                                {
                                                    "value": {
                                                        "name": "Holy Rage^Judas Priest^Atkins/May Project^",
                                                        "id": "https://ld.amazonalexa.com/entities/v1/5weB5rEfNVqDuk8WQEVprY"
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            },
                            {
                                "type": "Simple",
                                "value": "jack",
                                "resolutions": {
                                    "resolutionsPerAuthority": [
                                        {
                                            "authority": "AlexaEntities",
                                            "status": {
                                                "code": "ER_SUCCESS_MATCH"
                                            },
                                            "values": [
                                                {
                                                    "value": {
                                                        "name": "Jack",
                                                        "id": "https://ld.amazonalexa.com/entities/v1/3RAHxMlM8kNCNynNc67lEJ"
                                                    }
                                                },
                                                {
                                                    "value": {
                                                        "name": "Jack",
                                                        "id": "https://ld.amazonalexa.com/entities/v1/59kZG7GNVruEiv0I7DMyyn"
                                                    }
                                                },
                                                {
                                                    "value": {
                                                        "name": "Jack",
                                                        "id": "https://ld.amazonalexa.com/entities/v1/63nC6NdpAiDDfhWh3rH97o"
                                                    }
                                                },
                                                {
                                                    "value": {
                                                        "name": "Jack",
                                                        "id": "https://ld.amazonalexa.com/entities/v1/Aihij8TmUB7GGmc0NB2WAP"
                                                    }
                                                },
                                                {
                                                    "value": {
                                                        "name": "Jack",
                                                        "id": "https://ld.amazonalexa.com/entities/v1/IXkcQEfhx2kE8yHeOy5O9T"
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                },
                "__Conjunction": {
                    "name": "__Conjunction",
                    "value": "and",
                    "confirmationStatus": "NONE",
                    "source": "USER",
                    "slotValue": {
                        "type": "Simple",
                        "value": "and"
                    }
                }
            }
        }
    }""")
    fulfillment_component = _get_fulfillment_component()

    fulfillment_body_dict = _build_fulfillment_body_dict(LIST_SLOT_REQUEST__LIST_VALUE)
    body = fulfillment_schemas.from_dict(fulfillment_body_dict)
    intent = fulfillment_component.intent_from_fulfillment(body, lang=LanguageCode.ENGLISH)

    assert intent == MockGreetFriends(friend_names=["Al St. John", "Jack"])
    #                                                ^ that's what Alexa matched ..


#
# TODO
#

SLOTS_UNFILLED_REQUEST = json.loads("""{
    "type": "IntentRequest",
    "requestId": "amzn1.echo-api.request.8703689c-d01c-4362-8100-81e14e95087e",
    "locale": "en-US",
    "timestamp": "2021-08-11T21:44:34Z",
    "intent": {
        "name": "smalltalk_GreetFriends",
        "confirmationStatus": "NONE",
        "slots": {
            "friend_names": {
                "name": "friend_names",
                "confirmationStatus": "NONE"
            },
            "__Conjunction": {
                "name": "__Conjunction",
                "confirmationStatus": "NONE"
            }
        }
    }
}"""
)

UNMATCHED_CUSTOM_ENTITY_REQUEST = {
    'version': '1.0',
    'session': {'new': False, 'sessionId': 'amzn1.echo-api.session.fake-session-id', 'application': {'applicationId': 'amzn1.ask.skill.fake-application-id'}, 'user': {'userId': 'amzn1.ask.account.fake-account'}},
    'context': {
        'Viewports': [{'type': 'APL', 'id': 'main', 'shape': 'RECTANGLE', 'dpi': 213, 'presentationType': 'STANDARD', 'canRotate': False, 'configuration': {'current': {'mode': 'HUB', 'video': {'codecs': ['H_264_42', 'H_264_41']}, 'size': {'type': 'DISCRETE', 'pixelWidth': 1280, 'pixelHeight': 800}}}}],
        'Viewport': {'experiences': [{'arcMinuteWidth': 346, 'arcMinuteHeight': 216, 'canRotate': False, 'canResize': False}], 'mode': 'HUB', 'shape': 'RECTANGLE', 'pixelWidth': 1280, 'pixelHeight': 800, 'dpi': 213, 'currentPixelWidth': 1280, 'currentPixelHeight': 800, 'touch': ['SINGLE'], 'video': {'codecs': ['H_264_42', 'H_264_41']}},
        'Extensions': {'available': {'aplext:backstack:10': {}}},
        'System': {'application': {'applicationId': 'amzn1.ask.skill.fake-application-id'}, 'user': {'userId': 'amzn1.ask.account.fake-account'}, 'device': {'deviceId': 'amzn1.ask.device.fake-device-id', 'supportedInterfaces': {'Alexa.Presentation.APL': {'runtime': {'maxVersion': '1.7'}}}}, 'apiEndpoint': 'https://api.amazonalexa.com', 'apiAccessToken': 'fake-access-token'}
    },
    'request': {
        'type': 'IntentRequest',
        'requestId': 'amzn1.echo-api.request.fake-request-id',
        'locale': 'en-US',
        'timestamp': '2021-08-13T19:20:45Z',
        'intent': {
            'name': 'restaurant_OrderPizza',
            'confirmationStatus': 'NONE',
            'slots': {
                'amount': {
                    'name': 'amount',
                    'value': '2',
                    'confirmationStatus': 'NONE',
                    'source': 'USER',
                    'slotValue': {'type': 'Simple', 'value': '2'}
                },
                'pizza_type': {
                    'name': 'pizza_type',
                    'value': 'margherita pizzas',
                    'resolutions': {
                        'resolutionsPerAuthority': [{'authority': 'amzn1.er-authority.echo-sdk.amzn1.ask.skill.fake-application-id.PizzaType', 'status': {'code': 'ER_SUCCESS_NO_MATCH'}}]},
                        'confirmationStatus': 'NONE',
                        'source': 'USER',
                        'slotValue': {'type': 'Simple', 'value': 'margherita pizzas', 'resolutions': {'resolutionsPerAuthority': [{'authority': 'amzn1.er-authority.echo-sdk.amzn1.ask.skill.fake-application-id.PizzaType', 'status': {'code': 'ER_SUCCESS_NO_MATCH'}}]}}
                }
            }
        }
    }
}
