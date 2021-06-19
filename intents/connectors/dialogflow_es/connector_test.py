from unittest.mock import patch

from google.cloud.dialogflow_v2.types import DetectIntentResponse

from intents.connectors.dialogflow_es.connector import DialogflowEsConnector
from intents import language
from example_agent import ExampleAgent, travels

# A full Dialogflow Response, with
# - A text message in the DEFAULT platform
# - A text message in the TELEGRAM platform
# - A quick replies message in the TELEGRAM platform
df_response_quick_replies_serialized = b'\n-1cedb9e6-f958-437f-9299-74f966fbec62-9779ea79\x12\xa4\x03\n\x10i want to travel"\x00(\x012QIf you like I can recommend you an hotel. Or I can send you some holiday pictures:U\nS\nQIf you like I can recommend you an hotel. Or I can send you some holiday pictures:.\n*\n(I also like travels, how can I help you?0\x03:;\x1a7\n\rQuick Replies\x12\x12Recommend an hotel\x12\x12Send holiday photo0\x03Zl\nOprojects/learning-dialogflow/agent/intents/e3a1e749-be67-11eb-8ad8-bbef97dc13e7\x12\x19travels.user_wants_travele\x00\x00\x80?z\x02en'
df_response_quick_replies = DetectIntentResponse.deserialize(df_response_quick_replies_serialized)

# TODO: one with parameters and contexts

@patch("intents.connectors.dialogflow_es.connector.resolve_credentials")
@patch("intents.connectors.dialogflow_es.connector.EventInput")
@patch("intents.connectors.dialogflow_es.connector.QueryInput")
@patch("intents.connectors.dialogflow_es.connector.TextInput")
@patch("intents.connectors.dialogflow_es.connector.SessionsClient")
def test_predict(mock_df_client_class, *args):
    # TODO: this relies on the consistency between mock prediction and
    # ExampleAgent
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
    assert isinstance(predicted, travels.user_wants_travel)
    assert predicted.fulfillment_text == df_response_quick_replies.query_result.fulfillment_text
    assert predicted.prediction.fulfillment_messages == {
        language.IntentResponseGroup.DEFAULT: [
            language.TextIntentResponse(choices=["If you like I can recommend you an hotel. Or I can send you some holiday pictures"])
        ],
        language.IntentResponseGroup.RICH: [
            language.TextIntentResponse(choices=["I also like travels, how can I help you?"]),
            language.QuickRepliesIntentResponse(replies=["Recommend an hotel", "Send holiday photo"])
        ]
    }
