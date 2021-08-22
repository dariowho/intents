"""
Patches :class:`~intents.model.entity.Sys.MusicGenre`

Sources:

* https://www.musicgenreslist.com/
* https://blogs.transparent.com/chinese/music-genres-in-chinese/

"""
from typing import List, Union

from intents import Entity, LanguageCode
from intents.language.entity_language import make_language_data

# TODO: this is very incomplete

class I_IntentsMusicGenre(Entity):
    __intents_internal__ = True
    __entity_language_data__ = {
        LanguageCode.ENGLISH: make_language_data(["Classic", "Alternative", "Blues", "Opera", "Country", "Bluegrass", "Soul", "Rockabilly", ["Progressive", "Prog"], ["Progressive rock", "Prog rock"], ["Progressive metal", "Prog metal"], "Rock", ["Rock 'n' Roll", "Rock and Roll"], "Hard Rock", "Garage Rock", "Grunge", ["Heavy Metal", "Metal"], "Dance", "Dubstep", "Electroswing", "House", "Techno", "Trance", "Electronic", ["Funk", "Funky"], "Rap", ["Hip Hop", "Hip-Hop"], "Swing", "Lounge", "Drum & Bass", "Folk", "Pop", "Jazz", "Gospel", "Reggaeton", ["Brit Pop", "Britpop", "British Pop"], "Reggae", ["R&B", "Rhythm & Blues", "Rhythm and Blues"], "Ska", "Surf"]),
        LanguageCode.ITALIAN: make_language_data(["Elettronica", ["Musica classica", "Classica"], "Alternative", "Blues", "Opera", "Country", "Bluegrass", "Soul", "Rockabilly", ["Progressive", "Prog"], ["Rock progressivo", "Progressive rock", "Prog rock"], ["Progressive metal", "Prog metal"], "Rock", ["Rock 'n' Roll", "Rock and Roll"], "Hard Rock", "Garage Rock", "Grunge", ["Heavy Metal", "Metal"], "Dance", "Disco", "Dubstep", "Electroswing", "House", "Techno", "Trance", ["Funk", "Funky"], "Rap", ["Hip Hop", "Hip-Hop"], "Swing", "Lounge", "Drum & Bass", "Folk", "Pop", "Jazz", "Gospel", "Reggaeton", ["Brit Pop", "Britpop", "British Pop"], "Reggae", ["R&B", "Rhythm & Blues", "Rhythm and Blues"], "Ska", "Surf"]),
        LanguageCode.DUTCH: make_language_data([["Elektronische", "Elektronische muziek"], ["Klassieke", "Klassieke muziek"], "Alternative", "Blues", "Opera", "Country", "Bluegrass", "Soul", "Rockabilly", ["Progressive", "Prog"], ["Rock progressivo", "Progressive rock", "Prog rock"], ["Progressive metal", "Prog metal"], "Rock", ["Rock 'n' Roll", "Rock and Roll"], "Hard Rock", "Garage Rock", "Grunge", ["Heavy Metal", "Metal"], "Dance", "Disco", "Dubstep", "Electroswing", "House", "Techno", "Trance", ["Funk", "Funky"], "Rap", ["Hip Hop", "Hip-Hop"], "Swing", "Lounge", "Drum & Bass", "Folk", "Pop", "Jazz", "Gospel", "Reggaeton", ["Brit Pop", "Britpop", "British Pop"], "Reggae", ["R&B", "Rhythm & Blues", "Rhythm and Blues"], "Ska", "Surf"]),
        LanguageCode.FRENCH: make_language_data([["Musique électronique", "Electronica"], ["Musique classique", "Classique"], "Alternative", "Blues", ["Opéra", "Opera"], "Country", "Bluegrass", "Soul", "Rockabilly", ["Musique progressive", "Progressive", "Prog"], ["Rock progressive", "Progressive rock", "Prog rock"], ["Metal Progressive", "Progressive metal", "Prog metal"], "Rock", ["Rock 'n' Roll", "Rock and Roll"], "Hard Rock", "Garage Rock", "Grunge", ["Heavy Metal", "Metal"], "Dance", "Disco", "Dubstep", "Electroswing", "House", "Techno", "Trance", ["Funk", "Funky"], "Rap", ["Hip Hop", "Hip-Hop"], "Swing", "Lounge", "Drum & Bass", "Folk", "Pop", "Jazz", "Gospel", "Reggaeton", ["Brit Pop", "Britpop", "British Pop"], "Reggae", ["R&B", "Rhythm & Blues", "Rhythm and Blues"], "Ska", "Surf"]),
        LanguageCode.GERMAN: make_language_data([["Elektronische Musik", "elektronische"], ["klassische Musik", "klassische"], ["Opernmusik", "Opern"], ["Progressive", "Prog"], ["Progressive rock", "Prog rock"], ["Progressive metal", "Prog metal"], "Alternative", "Blues", "Country", "Bluegrass", "Soul", "Rockabilly", "Rock", ["Rock 'n' Roll", "Rock and Roll"], "Hard Rock", "Garage Rock", "Grunge", ["Heavy Metal", "Metal"], "Dance", "Disco", "Dubstep", "Electroswing", "House", "Techno", "Trance", ["Funk", "Funky"], "Rap", ["Hip Hop", "Hip-Hop"], "Swing", "Lounge", "Drum & Bass", "Folk", "Pop", "Jazz", "Gospel", "Reggaeton", ["Brit Pop", "Britpop", "British Pop"], "Reggae", ["R&B", "Rhythm & Blues", "Rhythm and Blues"], "Ska", "Surf"]),
        LanguageCode.SPANISH: make_language_data([["Música electrónica", "Electrónica", "Electronic", "Electro"], ["Música clásica", "Clásica"], ["Opera", "Musica de opera"], ["Progressive", "Prog"], ["Rock progresivo", "Progressive rock", "Prog rock"], ["Metal progresivo", "Progressive metal", "Prog metal"], "Alternative", "Blues", "Country", "Bluegrass", "Soul", "Rockabilly", "Rock", ["Rock 'n' Roll", "Rock and Roll"], "Hard Rock", "Garage Rock", "Grunge", ["Heavy Metal", "Metal"], "Dance", "Disco", "Dubstep", "Electroswing", "House", "Techno", "Trance", ["Funk", "Funky"], "Rap", ["Hip Hop", "Hip-Hop"], "Swing", "Lounge", "Drum & Bass", "Folk", "Pop", "Jazz", "Gospel", "Reggaeton", ["Brit Pop", "Britpop", "British Pop"], "Reggae", ["R&B", "Rhythm & Blues", "Rhythm and Blues"], "Ska", "Surf"]),
        LanguageCode.CHINESE: make_language_data(["另类", "兰草", "蓝调", "古典", "乡村", "轻", "电子", "民乐", "重金属", "嘻哈", "爵士", "歌剧", "流行", "说唱", "节奏布鲁斯", "雷鬼", "摇滚", "灵魂", "传统", "世界"]),
    }
