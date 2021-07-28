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
df_response_quick_replies_serialized = b'\n-1cedb9e6-f958-437f-9299-74f966fbec62-9779ea79\x12\xa4\x03\n\x10i want to travel"\x00(\x012QIf you like I can recommend you an hotel. Or I can send you some holiday pictures:U\nS\nQIf you like I can recommend you an hotel. Or I can send you some holiday pictures:.\n*\n(I also like travels, how can I help you?0\x03:;\x1a7\n\rQuick Replies\x12\x12Recommend an hotel\x12\x12Send holiday photo0\x03Zl\nOprojects/learning-dialogflow/agent/intents/e3a1e749-be67-11eb-8ad8-bbef97dc13e7\x12\x19travels.user_wants_travele\x00\x00\x80?z\x02en'
df_response_quick_replies = DetectIntentResponse.deserialize(df_response_quick_replies_serialized)

# CoffeeAgent "I'd like an espresso"
df_response_espresso_serialized = b'\n-c39d5684-4409-49bc-9095-08f39a506f7d-046d94d0\x12\x89\x02\n\x14I\'d like an espresso"\x00(\x012\x0cAny response:\x10\n\x0e\n\x0cAny responseR\\\nXprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_testing_askcoffee\x10\x05Zf\nOprojects/learning-dialogflow/agent/intents/ea48d872-ed7b-11eb-a79e-17bc86f5a601\x12\x13testing.AskEspressoe\x00\x00\x80?z\x02en'
df_response_espresso = DetectIntentResponse.deserialize(df_response_espresso_serialized)

# CoffeeAgent "I'd like an espresso" > "With milk"
df_response_espresso_milk_serialized = b'\n-317df591-6627-41fa-a8e1-880752978ee0-046d94d0\x12\xd6\x02\n\tWith milk"\x00(\x012\x0cAny response:\x10\n\x0e\n\x0cAny responseRZ\nVprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_testing_addmilk\x10\x05R\\\nXprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_testing_askcoffee\x10\x04Zb\nOprojects/learning-dialogflow/agent/intents/ea48d874-ed7b-11eb-a79e-17bc86f5a601\x12\x0ftesting.AddMilke\x00\x00\x80?z\x02en'
df_response_espresso_milk = DetectIntentResponse.deserialize(df_response_espresso_milk_serialized)

# CoffeeAgent "I'd like an espresso" > "With milk" > "And no foam"
df_response_espresso_milk_nofoam_serialized = b'\n-29024669-1dc0-470f-aea1-1386752072cd-046d94d0\x12\xda\x02\n\x0bAnd no foam"\x00(\x012\x0cAny response:\x10\n\x0e\n\x0cAny responseRZ\nVprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_testing_addmilk\x10\x04R\\\nXprojects/learning-dialogflow/agent/sessions/testing-session/contexts/c_testing_askcoffee\x10\x03Zd\nOprojects/learning-dialogflow/agent/intents/ea48d878-ed7b-11eb-a79e-17bc86f5a601\x12\x11testing.AndNoFoame\x00\x00\x80?z\x02en'
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
    assert isinstance(predicted.intent, travels.user_wants_travel)
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
