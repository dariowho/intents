import os
import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Union

import yaml

import intents
from intents.language import agent_language, LanguageCode
from intents.model.entity import _EntityMetaclass
from intents.model.intent import _IntentMetaclass

#
# Example Utterances
#

class UtteranceChunk:
    """
    An Example Utterance can be seen as a sequence of Chunks, where each Chunk
    is either a mapped Entity, or a plain text string.
    """

@dataclass
class TextUtteranceChunk(UtteranceChunk):
    """
    An Utterance Chunk that is a static, plain text string.
    """
    text: str

@dataclass
class EntityUtteranceChunk(UtteranceChunk):
    """
    An Utterance Chunk that is a matched entity
    """
    entity_cls: _EntityMetaclass
    parameter_name: str
    parameter_value: str

# TODO: check that parameter_value is one of the entries in custom entities
RE_EXAMPLE_PARAMETERS = re.compile(r"\$(?P<parameter_name>[\w]+)\{(?P<parameter_value>[^\}]+)\}")

class ExampleUtterance(str):
    """
    One of the example Utterances of a given Intent.
    """
    
    # TODO: check for escape characters - intent is possibly intent_cls
    def __init__(self, example: str, intent: intents.Intent):
        self._intent = intent
        self.chunks() # Will check parameters
    
    def __new__(cls, example: str, intent: intents.Intent):
        return super().__new__(cls, example)

    def chunks(self):
        """
        Return the Utterance as a sequence of :class:`UtteranceChunk`. Each
        chunk is either a plain text string, or a mapped Entity.

        >>> utterance = ExampleUtterance("My name is $user_name{Guido}!", intents.user_gives_name)
        >>> utterance.chunks()
        [
            TextUtteranceChunk(text="My name is "),
            EntityUtteranceChunk(entity_cls=Sys.Person, parameter_name="user_name", parameter_value="Guido"),
            TextUtteranceChunk(text="!")
        ]

        TODO: handle escaping
        """
        parameter_schema = self._intent.parameter_schema()
        result = []
        last_end = 0
        for m in RE_EXAMPLE_PARAMETERS.finditer(self):
            m_start, m_end = m.span()
            m_groups = m.groupdict()
            if m_start > 0:
                result.append(TextUtteranceChunk(text=self[last_end:m_start]))
            
            if (parameter_name := m_groups['parameter_name']) not in parameter_schema:
                raise ValueError(f"Example '{self}' references parameter ${parameter_name}, but intent {self._intent.name} does not define such parameter.")
 
            entity_cls = parameter_schema[parameter_name].entity_cls
            result.append(EntityUtteranceChunk(
                entity_cls=entity_cls,
                parameter_name=m_groups['parameter_name'],
                parameter_value=m_groups['parameter_value']
            ))

            last_end = m_end

        last_chunk = TextUtteranceChunk(text=self[last_end:])
        if last_chunk.text:
            result.append(last_chunk)

        return result

#
# Responses
#

class IntentResponseGroup(Enum):
    """
    Intent responses are divided in groups. The same intent can be answered with
    a set of plain-text responses (:var:`IntentResponseGroup.DEFAULT`), or with
    rich content (:var:`IntentResponseGroup.RICH`) that includes cards, images
    and quick replies.
    """
    DEFAULT = "default"
    RICH = "rich"

class IntentResponse:
    """
    One of the Response Utterances of a given Intent.
    """

class TextIntentResponse(IntentResponse):
    """
    A plain text response. The actual response is picked randomly from a pool of
    choices.
    """

    choices: List[str]

    def __init__(self, choices: Union[str, List[str]]):
        if not isinstance(choices, list):
            assert isinstance(choices, str)
            choices = [choices]

        self.choices = choices

    def __hash__(self):
        return "".join(self.choices).__hash__()

    def __eq__(self, other):
        if not isinstance(other, TextIntentResponse):
            return False
        return self.choices == other.choices
    
    def __str__(self):
        return f"<TextIntentResponse: {self.choices}>"

    def __repr__(self):
        return str(self)

class QuickRepliesIntentResponse(IntentResponse):
    """
    A set of Quick Replies that can be used to answer the Intent. Each reply
    must be shorter than 20 characters.
    """

    replies: List[str]

    def __init__(self, replies: List[str]):
        for rep in replies:
            if len(rep) > 20:
                raise ValueError(f"Quick Replies must be shorter than 20 chars. Quick reply '{rep}' is {len(rep)} chars long.")
        self.replies = replies

    def __hash__(self):
        return "".join(self.replies).__hash__()

    def __eq__(self, other):
        if not isinstance(other, QuickRepliesIntentResponse):
            return False
        return self.replies == other.replies
    
    def __str__(self):
        return f"<QuickRepliesIntentResponse: {self.replies}>"

    def __repr__(self):
        return str(self)

@dataclass
class IntentLanguageData:
    """
    Language data for an Intent consists of three resources:

    * Example Utterances
    * Slot Filling Prompts
    * Responses

    **Example Utterances** are the messages that Agent will be trained on to
    recognize the Intent.

    **Responses**, intuitively, are the Agent's response messages that will be sent
    to User once the Intent is recognized. They are divided in groups: a
    :var:`IntentResponseGroup.DEFAULT` group (mandatory) can only contain plain
    text responses. A :var:`IntentResponseGroup.RICH` group can provide intent
    responses that include cards, images and quick replies.

    **Slot Filling Promps** are used to solve parameters that couldn't be tagged in
    the original message. For instance a `order_pizza` intent may have a
    `pizza_type` parameter. When User asks "I'd like a pizza" we want to fill
    the slot by asking "What type of pizza?". `slot_filling_prompts` will map
    parameters to their prompts: `{"pizza_type": ["What type of pizza?"]}`
    """
    example_utterances: List[ExampleUtterance]
    slot_filling_prompts: Dict[str, List[str]]
    responses: Dict[IntentResponseGroup, List[IntentResponse]]

#
# Language Data Loader
#

def intent_language_data(agent_cls: "agent._AgentMetaclass", intent_cls: _IntentMetaclass, language_code: LanguageCode=None) -> Dict[LanguageCode, IntentLanguageData]:
    language_folder = agent_language.agent_language_folder(agent_cls)

    if not language_code:
        result = {}
        for language_code in agent_cls.languages:
            language_data = intent_language_data(agent_cls, intent_cls, language_code)
            result[language_code] = language_data[language_code]
        return result

    if isinstance(language_code, str):
        language_code = LanguageCode(language_code)

    language_file = os.path.join(language_folder, language_code.value, f"{intent_cls.name}.yaml")
    if not os.path.isfile(language_file):
        raise ValueError(f"Language file not found for intent '{intent_cls.name}'. Expected path: {language_file}. Language files are required even if the intent doesn't need language; in this case, use an empty file.")
    
    with open(language_file, 'r') as f:
        language_data = yaml.load(f.read(), Loader=yaml.FullLoader)

    if not language_data:
        return IntentLanguageData([], {}, [])

    examples_data = language_data.get('examples', [])
    responses_data = language_data.get('responses', [])

    try:
        examples = [ExampleUtterance(s, intent_cls) for s in examples_data]
        responses = _build_responses(responses_data)
    except Exception as e:
        raise RuntimeError(f"Failed to load language data for intent {intent_cls.name} (see stacktrace above for root cause).") from e

    language_data = IntentLanguageData(
        example_utterances=examples,
        slot_filling_prompts=language_data.get('slot_filling_prompts', {}),
        responses=responses
    )

    return {language_code: language_data}

def _build_responses(responses_data: dict):
    result = {}

    response_group: str
    responses: List[dict]
    for response_group, responses in responses_data.items():
        try:
            response_group = IntentResponseGroup(response_group)
        except ValueError as e:
            raise NotImplementedError(f"Unsupported Response Group '{response_group}' in 'responses'. Currently, only 'default' and 'rich' are supported")

        result[response_group] = []
        for r in responses:
            assert len(r) == 1
            for r_type, r_data in r.items():
                if r_type == 'text':
                    result[response_group].append(TextIntentResponse(r_data))
                elif r_type == 'quick_replies':
                    result[response_group].append(QuickRepliesIntentResponse(r_data))
                else:
                    raise NotImplementedError(f"Unsupported response type '{r_type}'. Currently, only 'text' is supported")
                
    return result
