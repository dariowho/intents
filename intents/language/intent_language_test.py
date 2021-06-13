import pytest
from intents.language.intent_language import TextIntentResponse, QuickRepliesIntentResponse, ImageIntentResponse, CardIntentResponse, CustomPayloadIntentResponse

def test_text_intent_response_string():
    text_response_instance = TextIntentResponse(["ciao"])
    text_response_from_yaml = TextIntentResponse.from_yaml("ciao")
    assert text_response_instance == text_response_from_yaml
    assert text_response_from_yaml.choices == ["ciao"]

def test_text_intent_response_list():
    text_response_instance = TextIntentResponse(["pippo", "franco"])
    text_response_from_yaml = TextIntentResponse.from_yaml(["pippo", "franco"])
    assert text_response_instance == text_response_from_yaml
    assert text_response_from_yaml.choices == ["pippo", "franco"]

def test_quick_replies_response_string():
    quick_replies_instance = QuickRepliesIntentResponse(["ciao"])
    quick_replies_from_yaml = QuickRepliesIntentResponse.from_yaml("ciao")
    assert quick_replies_instance == quick_replies_from_yaml
    assert quick_replies_from_yaml.replies == ["ciao"]

def test_quick_replies_response_list():
    quick_replies_response_instance = QuickRepliesIntentResponse(["pippo", "franco"])
    quick_replies_response_from_yaml = QuickRepliesIntentResponse.from_yaml(["pippo", "franco"])
    assert quick_replies_response_instance == quick_replies_response_from_yaml
    assert quick_replies_response_from_yaml.replies == ["pippo", "franco"]

def test_quick_replies_response_too_long():
    with pytest.raises(ValueError):
        QuickRepliesIntentResponse(["pippo", "franco", "chi chi chi, co co co"])
        
    with pytest.raises(ValueError):
        QuickRepliesIntentResponse.from_yaml(["chi chi chi, co co co", "pippo", "franco"])

    with pytest.raises(ValueError):
        QuickRepliesIntentResponse.from_yaml("chi chi chi, co co co")

def test_image_response_string():
    image_response_instance = ImageIntentResponse(url="https://example.com/image.png")
    image_response_from_yaml = ImageIntentResponse.from_yaml("https://example.com/image.png")
    assert image_response_instance == image_response_from_yaml

def test_image_response_dict():
    image_response_instance = ImageIntentResponse(url="https://example.com/image.png", title="A title")
    image_response_from_yaml = ImageIntentResponse.from_yaml({"url": "https://example.com/image.png", "title": "A title"})
    assert image_response_instance == image_response_from_yaml

def test_custom_payload_response():
    custom_payload_instance = CustomPayloadIntentResponse("any_name", {"foo": "bar"})
    custom_payload_from_yaml = CustomPayloadIntentResponse.from_yaml({
        "any_name": {"foo": "bar"}
    })
    assert custom_payload_instance == custom_payload_from_yaml

def test_card_intent_response():
    card_reponse_instance = CardIntentResponse("Card Title", "a subtitle...")
    card_reponse_from_yaml = CardIntentResponse.from_yaml({
        "title": "Card Title",
        "subtitle":"a subtitle..."
    })
    assert card_reponse_instance == card_reponse_from_yaml

def test_custom_payload_not_dict_data():
    with pytest.raises(ValueError):
        CustomPayloadIntentResponse.from_yaml("foo")

def test_custom_payload_not_dict_value():
    with pytest.raises(ValueError):
        CustomPayloadIntentResponse.from_yaml({"foo": "bar"})

def test_custom_payload_multiple_keys():
    with pytest.raises(ValueError):
        CustomPayloadIntentResponse.from_yaml({
            "any_name": {"foo": "bar"},
            "another_name": {"not": "allowed"}
        })
