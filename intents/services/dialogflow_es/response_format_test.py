from google.cloud.dialogflow_v2.types import DetectIntentResponse
from google.cloud.dialogflow_v2 import types as df_types

from intents.language import IntentResponseGroup, TextIntentResponse, QuickRepliesIntentResponse, CardIntentResponse
from intents.services.dialogflow_es.response_format import DialogflowTextResponse, \
    DialogflowQuickRepliesResponse, \
    DialogflowCardResponse, \
    intent_responses


# {'text': {'text': ['How about Hotel Belvedere, in Como?']}}
text_message_serialized = b'\n%\n#How about Hotel Belvedere, in Como?'
text_message = df_types.intent.Intent.Message.deserialize(text_message_serialized)
text_message_expected = TextIntentResponse(
    choices=['How about Hotel Belvedere, in Como?']
)

# {'text': {'text': ['I also like travels, how can I help you?']}, 'platform': 'TELEGRAM'}
text_message_rich_serialized = b'\n*\n(I also like travels, how can I help you?0\x03'
text_message_rich = df_types.intent.Intent.Message.deserialize(text_message_rich_serialized)
text_message_rich_expected = TextIntentResponse(
    choices=['I also like travels, how can I help you?']
)

# {'quickReplies': {'title': 'Quick Replies',
#   'quickReplies': ['Recommend an hotel', 'Send holiday photo']},
#  'platform': 'TELEGRAM'}
quick_replies_serialized = b'\x1a7\n\rQuick Replies\x12\x12Recommend an hotel\x12\x12Send holiday photo0\x03'
quick_replies_message = df_types.intent.Intent.Message.deserialize(quick_replies_serialized)
quick_replies_expected = QuickRepliesIntentResponse(
    replies=['Recommend an hotel', 'Send holiday photo']
)

# {'card': {'title': 'Hotel Belvedere',
#   'subtitle': '📍 Como, IT 💬 (42) 👍 ★★★★☆',
#   'imageUri': 'https://loremflickr.com/320/240/holiday',
#   'buttons': [{'text': '👁',
#     'postback': 'https://github.com/dariowho/intents'}]},
#  'platform': 'TELEGRAM'}
card_message_serialized = b'"\x95\x01\n\x0fHotel Belvedere\x12,\xf0\x9f\x93\x8d Como, IT \xf0\x9f\x92\xac (42) \xf0\x9f\x91\x8d \xe2\x98\x85\xe2\x98\x85\xe2\x98\x85\xe2\x98\x85\xe2\x98\x86\x1a\'https://loremflickr.com/320/240/holiday"+\n\x04\xf0\x9f\x91\x81\x12#https://github.com/dariowho/intents0\x03'
card_message = df_types.intent.Intent.Message.deserialize(card_message_serialized)
card_message_expected = CardIntentResponse(
    title='Hotel Belvedere',
    subtitle='📍 Como, IT 💬 (42) 👍 ★★★★☆',
    image='https://loremflickr.com/320/240/holiday',
    link='https://github.com/dariowho/intents'
)

df_response_quick_replies_serialized = b'\n-1cedb9e6-f958-437f-9299-74f966fbec62-9779ea79\x12\xa4\x03\n\x10i want to travel"\x00(\x012QIf you like I can recommend you an hotel. Or I can send you some holiday pictures:U\nS\nQIf you like I can recommend you an hotel. Or I can send you some holiday pictures:.\n*\n(I also like travels, how can I help you?0\x03:;\x1a7\n\rQuick Replies\x12\x12Recommend an hotel\x12\x12Send holiday photo0\x03Zl\nOprojects/learning-dialogflow/agent/intents/e3a1e749-be67-11eb-8ad8-bbef97dc13e7\x12\x19travels.user_wants_travele\x00\x00\x80?z\x02en'
df_response_quick_replies = DetectIntentResponse.deserialize(df_response_quick_replies_serialized)

def test_text_intent_response():
    result = DialogflowTextResponse.from_df_message(text_message.text)
    assert result == text_message_expected

    result = DialogflowTextResponse.from_df_message(text_message_rich.text)
    assert result == text_message_rich_expected

def test_quick_replies_response():
    result = DialogflowQuickRepliesResponse.from_df_message(quick_replies_message.quick_replies)
    assert result == quick_replies_expected

def test_card_response():
    result = DialogflowCardResponse.from_df_message(card_message.card)
    assert result == card_message_expected

def test_intent_responses():
    result = intent_responses(df_response_quick_replies)
    expected = {
        IntentResponseGroup.DEFAULT: [
            TextIntentResponse(choices=["If you like I can recommend you an hotel. Or I can send you some holiday pictures"])
        ],
        IntentResponseGroup.RICH: [
            TextIntentResponse(choices=["I also like travels, how can I help you?"]),
            QuickRepliesIntentResponse(replies=["Recommend an hotel", "Send holiday photo"])
        ]
    }
    assert result == expected
