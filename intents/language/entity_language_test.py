from intents.language.entity_language import make_language_data, EntityEntry

def test_make_entity_language_string_entries():
    entries = ["red", "green", "blue"]
    result = make_language_data(entries)
    expected = [
        EntityEntry(value="red", synonyms=[]),
        EntityEntry(value="green", synonyms=[]),
        EntityEntry(value="blue", synonyms=[])
    ]
    assert result == expected

def test_make_entity_language_list_entries():
    entries = [
        ["red", "crimson", "scarlett"],
        ["green", "emerald"],
        ["blue", "cyan", "azure"]
    ]
    result = make_language_data(entries)
    expected = [
        EntityEntry(value="red", synonyms=["crimson", "scarlett"]),
        EntityEntry(value="green", synonyms=["emerald"]),
        EntityEntry(value="blue", synonyms=["cyan", "azure"])
    ]
    assert result == expected

def test_make_entity_language_mixed_entries():
    entries = [
        ["red", "crimson", "scarlett"],
        "green",
        ["blue", "cyan", "azure"]
    ]
    result = make_language_data(entries)
    expected = [
        EntityEntry(value="red", synonyms=["crimson", "scarlett"]),
        EntityEntry(value="green", synonyms=[]),
        EntityEntry(value="blue", synonyms=["cyan", "azure"])
    ]
    assert result == expected
