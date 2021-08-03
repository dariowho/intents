"""
Here we define dataclass schemas for the Snips NLU Agent format. These are used
to produce JSON Dataset that can be read by Snips NLU.

References:

* https://github.com/snipsco/snips-nlu/blob/master/snips_nlu_samples/sample_dataset.json
* https://snips-nlu.readthedocs.io/en/latest/dataset.html
"""
from typing import List, Dict, Union
from dataclasses import dataclass, field

import dacite
from intents.helpers.data_classes import OmitNone

#
# Intent
#

@dataclass
class DatasetIntentUtteranceTextSegment:
    text: str

@dataclass
class DatasetIntentUtteranceEntitySegment:
    text: str
    entity: str
    slot_name: str

@dataclass
class DatasetIntentUtterance:
    data: List[Union[DatasetIntentUtteranceEntitySegment, DatasetIntentUtteranceTextSegment]]

@dataclass
class DatasetIntent:
    utterances: List[DatasetIntentUtterance]

#
# Entity
#

@dataclass
class DatasetEntityEntry:
    value: str
    synonyms: List[str] = field(default_factory=list)

@dataclass
class DatasetEntity:
    use_synonyms: bool
    automatically_extensible: bool
    matching_strictness: float
    data: List[DatasetEntityEntry] = OmitNone()

#
# Dataset
#

@dataclass
class Dataset:
    intents: Dict[str, DatasetIntent]
    entities: Dict[str, Union[DatasetEntity, dict]]
    language: str

def from_dict(data: dict):
    return dacite.from_dict(Dataset, data)

# import json
# # from intents.connectors._experimental.snips.agent_format import from_dict
# a = from_dict(json.load(open('/home/dario/lavoro/snips-sandbox/agent.json')))