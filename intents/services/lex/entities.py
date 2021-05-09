"""
Here we define mappings for Lex Built-in Slot Types (System Entities).
Reference:
https://docs.aws.amazon.com/lex/latest/dg/howitworks-builtins-slots.html

Note that Lex slot types aren't consistent across languages. Some are available
for all supported languages, some for US English only, others for all languages
except US English.
"""
from intents import Sys
from intents.prediction_service import StringEntityMapping, ServiceEntityMappings

MAPPINGS = ServiceEntityMappings.from_list([
    # StringEntityMapping(Sys.Any, "sys.any"),
    StringEntityMapping(Sys.Integer, "AMAZON.NUMBER"),
    StringEntityMapping(Sys.Person, "AMAZON.FirstName"), # TODO: expand to first name + last name
    # StringEntityMapping(Sys.MusicArtist, "sys.music-artist"),
    # StringEntityMapping(Sys.MusicGenre, "sys.music-genre"),
])
