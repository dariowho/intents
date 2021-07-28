from unittest.mock import patch

from google.cloud.dialogflow_v2.types import DetectIntentResponse

from intents.connectors.dialogflow_es.connector import DialogflowEsConnector
from intents import language
from intents.service_connector import Prediction
from intents.helpers import coffee_agent
from example_agent import ExampleAgent, travels

# A full Dialogflow Response from ExampleAgent, with
# - A text message in the DEFAULT platform
# - A text message in the TELEGRAM platform
# - A quick replies message in the TELEGRAM platform
df_response_quick_replies_serialized = b'\n-1cedb9e6-f958-437f-9299-74f966fbec62-9779ea79\x12\xa2\x03\n\x10i want to travel"\x00(\x012QIf you like I can recommend you an hotel. Or I can send you some holiday pictures:U\nS\nQIf you like I can recommend you an hotel. Or I can send you some holiday pictures:.\n*\n(I also like travels, how can I help you?0\x03:;\x1a7\n\rQuick Replies\x12\x12Recommend an hotel\x12\x12Send holiday photo0\x03Zj\nOprojects/learning-dialogflow/agent/intents/e3a1e749-be67-11eb-8ad8-bbef97dc13e7\x12\x17travels.UserWantsTravele\x00\x00\x80?z\x02en'
df_response_quick_replies = DetectIntentResponse.deserialize(df_response_quick_replies_serialized)

# CoffeeAgent "I'd like an espresso"
df_response_espresso_serialized = b'\n-8939a534-88f9-4e49-8ad1-eaec18543743-c4f60134\x12\xc1\x03\n\x14I\'d like an espresso"\x13\n\x11\n\x05roast\x12\x08\x1a\x06medium(\x012\x0cAny response:\x10\n\x0e\n\x0cAny responseR\x7f\nPprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_askcoffee\x10\x05\x1a)\n\x11\n\x05roast\x12\x08\x1a\x06medium\n\x14\n\x0eroast.original\x12\x02\x1a\x00R\x87\x01\nXprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_testing_askcoffee\x10\x04\x1a)\n\x11\n\x05roast\x12\x08\x1a\x06medium\n\x14\n\x0eroast.original\x12\x02\x1a\x00Z^\nOprojects/learning-dialogflow/agent/intents/9d3fe183-efd1-11eb-a79e-17bc86f5a601\x12\x0bAskEspressoe\x00\x00\x80?z\x02en'
df_response_espresso = DetectIntentResponse.deserialize(df_response_espresso_serialized)

# CoffeeAgent "I'd like an espresso" > "With milk"
df_response_espresso_milk_serialized = b'\n-2478f1c9-6549-4f7d-90c8-9fd493f66a42-c4f60134\x12\xf3\x03\n\tWith milk"\x00(\x012\x0cAny response:\x10\n\x0e\n\x0cAny responseRR\nNprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_addmilk\x10\x05R\x7f\nPprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_askcoffee\x10\x04\x1a)\n\x14\n\x0eroast.original\x12\x02\x1a\x00\n\x11\n\x05roast\x12\x08\x1a\x06mediumR\x87\x01\nXprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_testing_askcoffee\x10\x03\x1a)\n\x11\n\x05roast\x12\x08\x1a\x06medium\n\x14\n\x0eroast.original\x12\x02\x1a\x00ZZ\nOprojects/learning-dialogflow/agent/intents/9d3fe186-efd1-11eb-a79e-17bc86f5a601\x12\x07AddMilke\x00\x00\x80?z\x02en'
df_response_espresso_milk = DetectIntentResponse.deserialize(df_response_espresso_milk_serialized)

# CoffeeAgent "I'd like an espresso" > "With milk" > "And no foam"
df_response_espresso_milk_nofoam_serialized = b'\n-05c5d723-2f30-4d65-a590-6429a445144b-c4f60134\x12\xf7\x03\n\x0bAnd no foam"\x00(\x012\x0cAny response:\x10\n\x0e\n\x0cAny responseR\x7f\nPprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_askcoffee\x10\x03\x1a)\n\x11\n\x05roast\x12\x08\x1a\x06medium\n\x14\n\x0eroast.original\x12\x02\x1a\x00R\x87\x01\nXprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_testing_askcoffee\x10\x02\x1a)\n\x14\n\x0eroast.original\x12\x02\x1a\x00\n\x11\n\x05roast\x12\x08\x1a\x06mediumRR\nNprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_addmilk\x10\x04Z\\\nOprojects/learning-dialogflow/agent/intents/9d3fe18a-efd1-11eb-a79e-17bc86f5a601\x12\tAndNoFoame\x00\x00\x80?z\x02en'
df_response_espresso_milk_nofoam = DetectIntentResponse.deserialize(df_response_espresso_milk_nofoam_serialized)

#
# Tests
#

@patch("intents.connectors.dialogflow_es.connector.resolve_credentials")
@patch("intents.connectors.dialogflow_es.connector.EventInput")
@patch("intents.connectors.dialogflow_es.connector.QueryInput")
@patch("intents.connectors.dialogflow_es.connector.TextInput")
@patch("intents.connectors.dialogflow_es.connector.SessionsClient")
def test_predict(mock_df_client_class, *args):
    # TODO: this relies on the consistency between mock prediction and
    # ExampleAgent, consider switching to CoffeeAgent
    # TODO: this is more functional test than unit test...
    def mock_df_client():
        pass
    def mock_detect_intent(session, query_input):
        return df_response_quick_replies
    def mock_session_path(gcp_project_id, session):
        return 'fake-full-session-path'
    mock_df_client.detect_intent = mock_detect_intent
    mock_df_client.session_path = mock_session_path
    mock_df_client_class.return_value = mock_df_client

    df = DialogflowEsConnector('/fake/path/to/credentials.json', ExampleAgent)
    predicted = df.predict("A fake sentence")
    assert isinstance(predicted.intent, travels.UserWantsTravel)
    assert predicted.fulfillment_text == df_response_quick_replies.query_result.fulfillment_text
    assert predicted.fulfillment_message_dict == {
        language.IntentResponseGroup.DEFAULT: [
            language.TextIntentResponse(choices=["If you like I can recommend you an hotel. Or I can send you some holiday pictures"])
        ],
        language.IntentResponseGroup.RICH: [
            language.TextIntentResponse(choices=["I also like travels, how can I help you?"]),
            language.QuickRepliesIntentResponse(replies=["Recommend an hotel", "Send holiday photo"])
        ]
    }

@patch("intents.connectors.dialogflow_es.connector.resolve_credentials")
@patch("intents.connectors.dialogflow_es.connector.EventInput")
@patch("intents.connectors.dialogflow_es.connector.QueryInput")
@patch("intents.connectors.dialogflow_es.connector.TextInput")
@patch("intents.connectors.dialogflow_es.connector.SessionsClient")
def test_predict_related_intents_follow(mock_df_client_class, *args):
    def mock_df_client():
        pass
    def mock_detect_intent(session, query_input):
        return df_response_espresso_milk_nofoam # AskEspresso > WithMilk > AndNoFoam
    def mock_session_path(gcp_project_id, session):
        return 'testing-session'
    mock_df_client.detect_intent = mock_detect_intent
    mock_df_client.session_path = mock_session_path
    mock_df_client_class.return_value = mock_df_client

    df = DialogflowEsConnector('/fake/path/to/credentials.json', coffee_agent.CoffeeAgent)
    predicted = df.predict("A fake sentence")
    intent: coffee_agent.AndNoFoam = predicted.intent
    assert isinstance(intent, coffee_agent.AndNoFoam)
    assert isinstance(intent.parent_add_milk, coffee_agent.AddMilk)
    assert isinstance(intent.parent_add_milk.parent_ask_coffee, coffee_agent.AskCoffee) # TODO: or should be AskEspresso?
    assert intent.parent_add_milk.parent_ask_coffee.roast == "medium"

@patch("intents.connectors.dialogflow_es.connector.resolve_credentials")
def test_intent_need_context(m_credentials):
    df = DialogflowEsConnector('/fake/path/to/credentials.json', coffee_agent.CoffeeAgent)
    assert df._intent_needs_context(coffee_agent.AskCoffee) == True
    assert df._intent_needs_context(coffee_agent.AskEspresso) == False
    assert df._intent_needs_context(coffee_agent.AddMilk) == True
    assert df._intent_needs_context(coffee_agent.AddSkimmedMilk) == False
    assert df._intent_needs_context(coffee_agent.AndNoFoam) == False
#
# Prediction
#

def test_fulfillment_messages():
    mock_default_messages = [
        language.TextIntentResponse(choices=["If you like I can recommend you an hotel. Or I can send you some holiday pictures"])
    ]
    mock_rich_messages = [
        language.TextIntentResponse(choices=["I also like travels, how can I help you?"]),
        language.QuickRepliesIntentResponse(replies=["Recommend an hotel", "Send holiday photo"])
    ]
    prediction = Prediction(
        intent=None,
        confidence=0.5,
        fulfillment_message_dict={
            language.IntentResponseGroup.DEFAULT: mock_default_messages,
            language.IntentResponseGroup.RICH: mock_rich_messages
        },
        fulfillment_text="Fake fulfillment text"
    )

    assert prediction.fulfillment_messages() == mock_rich_messages
    assert prediction.fulfillment_messages(language.IntentResponseGroup.DEFAULT) == mock_default_messages
    assert prediction.fulfillment_messages(language.IntentResponseGroup.RICH) == mock_rich_messages
