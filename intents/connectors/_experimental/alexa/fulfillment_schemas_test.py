import json
from datetime import datetime

from intents.connectors._experimental.alexa import fulfillment_schemas as fs

def test_parse_docs_request():
    """
    This is the request at
    https://developer.amazon.com/en-US/docs/alexa/custom-skills/request-and-response-json-reference.html#request-body-syntax
    
    Request field has been replaced with actual IntentRequest
    """

    body = json.loads("""{
        "version": "1.0",
        "session": {
            "new": true,
            "sessionId": "amzn1.echo-api.session.[unique-value-here]",
            "application": {
            "applicationId": "amzn1.ask.skill.[unique-value-here]"
        },
        "attributes": {
            "key": "string value"
        },
        "user": {
            "userId": "amzn1.ask.account.[unique-value-here]",
            "accessToken": "Atza|AAAAAAAA...",
            "permissions": {
                "consentToken": "ZZZZZZZ..."
            }
        }
        },
        "context": {
            "System": {
            "device": {
                "deviceId": "string",
                "supportedInterfaces": {
                "AudioPlayer": {}
                }
            },
            "application": {
                "applicationId": "amzn1.ask.skill.[unique-value-here]"
            },
            "user": {
                "userId": "amzn1.ask.account.[unique-value-here]",
                "accessToken": "Atza|AAAAAAAA...",
                "permissions": {
                "consentToken": "ZZZZZZZ..."
                }
            },
            "person": {
                "personId": "amzn1.ask.person.[unique-value-here]",
                "accessToken": "Atza|BBBBBBB..."
            },
            "unit": {
                "unitId": "amzn1.ask.unit.[unique-value-here]",
                "persistentUnitId" : "amzn1.alexa.unit.did.[unique-value-here]"
            },
            "apiEndpoint": "https://api.amazonalexa.com",
            "apiAccessToken": "AxThk..."
            },
            "AudioPlayer": {
                "playerActivity": "PLAYING",
                "token": "audioplayer-token",
                "offsetInMilliseconds": 0
            }
        },
        "request": {
            "type": "IntentRequest",
            "requestId": "amzn1.echo-api.request.fake-request-id",
            "locale": "en-US",
            "timestamp": "2021-08-10T19:12:25Z",
            "intent": {
                "name": "smalltalk_hello",
                "confirmationStatus": "NONE"
            }
        }
    }""")

    expected = fs.FulfillmentBody(
        version="1.0",
        session=fs.FulfillmentSession(
            new=True,
            sessionId="amzn1.echo-api.session.[unique-value-here]",
            application=fs.FulfillmentSessionApplication(applicationId="amzn1.ask.skill.[unique-value-here]"),
            attributes={"key": "string value"},
            user=fs.FulfillmentSessionUser(
                userId="amzn1.ask.account.[unique-value-here]",
                accessToken="Atza|AAAAAAAA...",
                permissions={"consentToken": "ZZZZZZZ..."}
            )
        ),
        context=fs.FulfillmentContext(
            System=fs.FulfillmentContextSystem(
                apiAccessToken="AxThk...",
                apiEndpoint="https://api.amazonalexa.com",
                application=fs.FulfillmentContextSystemApplication(applicationId="amzn1.ask.skill.[unique-value-here]"),
                device=fs.FulfillmentContextSystemDevice(
                    deviceId="string",
                    supportedInterfaces={
                        "AudioPlayer": {}
                    }
                ),
                unit=fs.FulfillmentContextSystemUnit(
                    unitId="amzn1.ask.unit.[unique-value-here]",
                    persistentUnitId="amzn1.alexa.unit.did.[unique-value-here]"
                ),
                person=fs.FulfillmentContextSystemPerson(
                    personId="amzn1.ask.person.[unique-value-here]",
                    accessToken="Atza|BBBBBBB..."
                ),
                user=fs.FulfillmentContextSystemUser(
                    userId="amzn1.ask.account.[unique-value-here]",
                    accessToken="Atza|AAAAAAAA...",
                    permissions={
                       "consentToken": "ZZZZZZZ..."
                    }
                )
            ),
            AudioPlayer=fs.FulfillmentContextAudioPlayer(
                token="audioplayer-token",
                playerActivity=fs.PlayerActivity.PLAYING,
                offsetInMilliseconds=0
            )
        ),
        request=fs.FulfillmentIntentRequest(
            type=fs.RequestType.INTENT,
            requestId="amzn1.echo-api.request.fake-request-id",
            timestamp=datetime(year=2021, month=8, day=10, hour=19, minute=12, second=25),
            locale="en-US",
            intent=fs.FulfillmentIntentRequestIntent(
                name="smalltalk_hello",
                confirmationStatus=fs.IntentConfirmationStatus.NONE
            )
        )
    )

    assert fs.from_dict(body) == expected
