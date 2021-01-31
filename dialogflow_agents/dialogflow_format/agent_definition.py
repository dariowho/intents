"""
Here we define classes that marshal the output format of Dialogflow Agents. We use
these to generate a set of JSON files representing the agent, in a format that is compatible
with the ones you get from Settings > Export in the Dialogflow console.

A Dialogflow Agent is represented by a compressed folder that contains the Agent
metadata, a set of Intents and a set of Entities.

Agent **metadata** are stored in a `agent.json` file. A complementary
`package.json` contains a standard `{"version": "1.0.0"}`. TODO: model metadata.

Intents can be found in the `intents/` folder. Each **intent** is defined by 2 files:

* `intents/<INTENT_NAME>.json` contains the Intent definition. This is modelled in :class:`Intent`
* `intents/<INTENT_NAME>_usersays.json` contains the list of example utterances. Each
  utterance is modelled in :class:`IntentUsersays`

Entities can be found in the `entities/` folder. Each **entity** is defined by 2
files:

* `entities/<ENTITY_NAME>.json` contains the Entity definition, this is modelled
  in :class:`Entity`
* `entities/<ENTITY_NAME>_entries.json` contains the entity values and their synonyms
"""

from dataclasses import dataclass, field
from typing import List, Union

LANG = "en"

#
# entities/<ENTITY_NAME>.json
#

@dataclass
class Entity:
    id: str
    name: str
    isOverridable: bool = True
    isEnum: bool = False
    isRegexp: bool = False
    automatedExpansion: bool = False
    allowFuzzyExtraction: bool = False


#
# entities/<ENTITY_NAME>_entries_en.json
#

@dataclass
class EntityEntry:
    value: str
    synonyms: List[str]

#
# intents/<INTENT_NAME>.json
#

@dataclass
class Context:
    name: str
    lifespan: int = 2

@dataclass
class Prompt:
    value: str
    lang: str = LANG

@dataclass
class Parameter:
    id: str
    name: str
    required: bool
    dataType: str
    value: str
    defaultValue: str = ""
    isList: bool = False
    prompts: List[Prompt] = field(default_factory=list)
    promptMessages: List = field(default_factory=list)
    noMatchPromptMessages: List = field(default_factory=list)
    noInputPromptMessages: List = field(default_factory=list)
    outputDialogContexts: List = field(default_factory=list)


@dataclass
class ResponseMessage:
    speech: List[str]
    type: str = "0"
    title: str = ""
    textToSpeech: str = ""
    lang: str = LANG
    condition: str = ""


@dataclass
class Response:
    affectedContexts: List[Context]
    parameters: List[Parameter]
    messages: List[ResponseMessage]
    speech: List = field(default_factory=list)
    resetContexts: bool = False
    action: str = ""


@dataclass
class Intent:
    id: str
    name: str
    responses: List[Response]
    auto: bool = True
    contexts: List = field(default_factory=list)
    priority: int = 500000
    webhookUsed: bool = True
    webhookForSlotFilling: bool = True
    fallbackIntent: bool = False
    events: List[str] = field(default_factory=list)
    conditionalResponses: List = field(default_factory=list)
    condition: str = ""
    conditionalFollowupEvents: List = field(default_factory=list)

#
# intents/<INTENT_NAME>_usersays.json
#

@dataclass
class UsersaysEntityChunk:
    text: str
    meta: str
    alias: str
    userDefined: bool


@dataclass
class UsersaysTextChunk:
    text: str
    userDefined: bool


@dataclass
class IntentUsersays:
    id: str
    data: List[Union[UsersaysTextChunk, UsersaysEntityChunk]]
    isTemplate: bool = False
    count: int = 0
    lang: str = LANG
    updated: int = 0
