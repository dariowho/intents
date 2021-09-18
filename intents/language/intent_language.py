"""
**Intent** language files have the following structure:

.. code-block:: yaml

    examples:
      - an example utterance
      - another example utterance
      - an example utterance with $foo{42} as a numeric parameter

    slot_filling_prompts:
      foo:
        - Tell me the value for "foo"

    responses:
      default:
        - text:
          - A plain text response
          - An alternative response
          - Another alternative, referencing $foo as a paramneter
      rich:
        - text:
          - A text response for rich clients
        - quick_replies:
          - a reply chip
          - another reply chip

Let's look at the sections of this file.

* **examples** contain example utterances that will be used to predict the given
  intent. If your intent has a parameter, it can be referenced as
  $parameter_name{example value}. You can omit this section if your intent is
  not meant to be predicted (some intents are trigger-only)
* **slot_filling_prompt** are used when your intent has a mandatory parameter,
  and this parameter could not be matched in the user message. These prompts
  will be used to ask the User about that parameter. You can omit this section
  if your intent has no mandatory parameters, or if you don't want to define
  custom prompts.
* **responses** contain messages that Agent will send to User in response to the
  Intent. Two response groups are available:

  * **default** can only contain plain-text messages. It is good practice to
    always provide text-only response for situations where rich ones can't be rendered,
    such as vocal assistants, smartphone notifications and such. The `text`
    response type is specified in :class:`TextIntentResponse`
  * **rich** responses allow some extra types:
    :class:`QuickRepliesIntentResponse`, :class:`ImageIntentResponse`,
    :class:`CardIntentResponse` and :class:`CustomPayloadIntentResponse`

"""
import os
import re
import random
import logging
import warnings
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Union, Tuple, Type

import yaml

# pylint: disable=unused-import
import intents # Needed to generate docs
from intents import Intent, EntityMixin
from intents.language import agent_language, LanguageCode

logger = logging.getLogger(__name__)

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
    entity_cls: Type[EntityMixin]
    parameter_name: str
    parameter_value: str

# TODO: check that parameter_value is one of the entries in custom entities
RE_EXAMPLE_PARAMETERS = re.compile(r"\$(?P<parameter_name>[\w]+)\{(?P<parameter_value>[^\}]+)\}")

class ExampleUtterance(str):
    """
    One of the example Utterances of a given Intent.
    """
    
    # TODO: check for escape characters - intent is possibly intent_cls
    def __init__(self, example: str, intent: Intent):
        self._intent = intent
        self.chunks() # Will check parameters
    
    def __new__(cls, example: str, intent: Intent):
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

        .. warning::

            This method doesn't handle escaping yet.
        """
        # TODO: handle escaping
        parameter_schema = self._intent.parameter_schema
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
    a set of plain-text responses (:const:`IntentResponseGroup.DEFAULT`), or with
    rich content (:const:`IntentResponseGroup.RICH`) that includes cards, images
    and quick replies.
    """
    DEFAULT = "default"
    RICH = "rich"

class IntentResponse:
    """
    One of the Response Utterances of a given Intent.
    """

    @classmethod
    def from_yaml(cls, data: dict):
        """
        Instantiate an IntentResponse from language data, as it's found in its
        YAML file. Typically, IntentResponse is a dataclass and `data` is a dict
        of fields; however specific subclasses may override with custom
        parameters.

        Args:
            data: A response object, as it is read from the YAML file
        """
        return cls(**data)

    def render(self, intent: Intent):
        """
        Render the Response object by replacing parameter references with values from the give :class:`Intent`
        instance. This is done on every member of the Response class.

        As `IntentResponse` objects are frozen, `self` won't change. Instead a **new object** will be returned,
        with rendered members.

        .. warning::

            This function currently doesn't handle escaping.

        .. code-block:: python

                >>> intent = OrderCoffee(roast="dark")   # This typically comes from a Prediction
                >>> response = TextIntentResponse(choices=["I like $roast roasted coffee as well", "$roast roast, good choice!"]
                >>> response.render(intent)
                TextIntentResponse(choices=["I like dark roasted coffee as well", "dark roast, good choice!"])

        Args:
            intent: The Intent instance that will be used to read parameter values
        """
        # TODO: handle list/dict values differently
        parameter_dict = {k: intent.__dict__[k] for k in intent.parameter_schema}
        result_args = {}
        try:
            dataclass_fields = getattr(self, "__dataclass_fields__")
        except AttributeError as exc:
            raise ValueError(f"Response '{self}' doesn't seem to be a dataclass. If this is a "
                             "custom IntentResponse class, make sure to add a @dataclass decorator; "
                             "otherwise, please file an issue on the Intents repository.") from exc
        for field_name in dataclass_fields:
            if isinstance(field_name, (str, list)):
                result_args[field_name] = _render_response(
                    self.__dict__[field_name],
                    parameter_dict
                )
            else:
                result_args[field_name] = self.__dict__[field_name]
        return self.__class__(**result_args)

def _render_response(data: Union[str, list], parameter_dict: Dict[str, str]):
    """
    Render some response data by replacing parameter references with the one contained in `parameter_dict`. This
    function is called by :meth:`IntentResponse.render` on each of the Response members.
    """
    if not data:
        return data
        
    if isinstance(data, str):
        result = data
        for k, v in parameter_dict.items():
            # result = result.replace(f"${k}", str(v))  # TODO: handle escaping
            result = re.sub(r"(?:(?<=[^\w])|^)\$%s(?:(?=[^\w])|$)" % k, str(v), result)
        return result

    if isinstance(data, list):
        return [_render_response(x, parameter_dict) for x in data]

    raise NotImplementedError(f"Unsupported IntentResponse member type: `{type(data)}`. "
                              "Please open an issue at the Intents repository")

@dataclass(frozen=True)
class TextIntentResponse(IntentResponse):
    """
    A plain text response. The actual response is picked randomly from a pool of
    choices.

    In the YAML definition a text response can either be a string, as in

    .. code-block:: yaml

        responses:
          default:
            - text: This is a response

    Or a list of choices (the output fulfillment message will be chosen
    randomly among the different options)

    .. code-block:: yaml

        responses:
          default:
            - text:
              - This is a response
              - This is an alternative response

    Args:
        choices: A list of equivalent responses. One will be chosen at random at
            prediction time
    """

    choices: List[str]

    @classmethod
    def from_yaml(cls, data: Union[str, List[str]]):
        if isinstance(data, str):
            return cls([data])

        assert isinstance(data, list)
        return cls(data)

    def random(self):
        """
        Pick one of the available choices. It is recommended to :meth:`~IntentResponse.render` the response first.

        .. code-block:: python

            >>> intent = OrderCoffee(roast="dark")   # This typically comes from a Prediction
            >>> response = TextIntentResponse(choices=["I like $roast roasted coffee as well", "$roast roast, good choice!"]
            >>> response.render(intent).random()
            "dark roast, good choice!"
        """
        return random.choice(self.choices)

@dataclass(frozen=True)
class QuickRepliesIntentResponse(IntentResponse):
    """
    A set of Quick Replies that can be used to answer the Intent. Each reply
    must be shorter than 20 characters.

    In the YAML definition a quick replies response can either be a string, as in

    .. code-block:: yaml

        rich:
          - quick_replies: Order Pizza

    Or a list of replies, that will be rendered as separate chips

    .. code-block:: yaml

        rich:
          - quick_replies:
            - Order Pizza
            - Order Beer

    Args:
        replies: A list of possible User replies to the current intent 
    """

    replies: List[str]

    def __post_init__(self):
        # TODO: find policy for rendered replies
        for rep in self.replies:
            if len(rep) > 20:
                raise ValueError(f"Quick Replies must be shorter than 20 chars. Quick reply '{rep}' is {len(rep)} chars long.")

    @classmethod
    def from_yaml(cls, data: Union[str, List[str]]):
        if isinstance(data, str):
            return cls([data])
        
        assert isinstance(data, list)
        return cls(data)

@dataclass(frozen=True)
class ImageIntentResponse(IntentResponse):
    """
    A simple image, defined by its URL and an optional title

    In the YAML definition an image response can either be a string with the
    image URL, as in

    .. code-block:: yaml

        rich:
          - image: https://example.com/image.png

    Or an object with the image URL and a title, as in

    .. code-block:: yaml

        rich:
          - image:
              url: https://example.com/image.png
              title: An example image
    
    Args:
        url: A publicly accessible image URL
        title: A title for the image
    """
    url: str
    title: str = None

    @classmethod
    def from_yaml(cls, data: Union[str, List[str]]):
        if isinstance(data, str):
            return cls(url=data)
        
        assert isinstance(data, dict)
        return cls(**data)

@dataclass(frozen=True)
class CardIntentResponse(IntentResponse):
    """
    A simple content card that can be rendered on many platforms.

    In the YAML, this is defined as

    Or an object with the image URL and a title, as in

    .. code-block:: yaml

        rich:
          - card:
              title: The card title
              subtitle: An optional subtitle
              image: https://example.com/image.jpeg
              link: https://example.com/

    Args:
        title: The card title
        subtitle: A short subtitle
        image: URL of an image to be used as cover
        link: A link to follow if User taps the card
    """
    title: str
    subtitle: str = None
    image: str = None
    link: str = None

@dataclass(frozen=True)
class CustomPayloadIntentResponse(IntentResponse):
    """
    Custom Payloads are objects with arbitrary fields, they are supported by
    Dialogflow in every response group, including "Default". Currently they can
    only be defined in the YAML as free form payloads; support for marshalling
    or generation from code is expected in future developments.

    Args:
        name: A name that identifies the payload type
        payload: Any JSON-serializable object
    """

    name: str
    payload: dict

    @classmethod
    def from_yaml(cls, data: Dict[str, dict]):
        """
        In the YAML definition a custom payload is defined as follows

        .. code-block:: yaml

            rich:
              - custom:
                  custom_location:
                    latitude: 45.484907
                    longitude: 9.203299
                    name: Piazza Duca D'Aosta, Milano

        NOTE: while not currently enforced, consistency is expected between
        payload names and their fields. Future versions of the library will
        marshal custom payloads against dataclass schemas.
        """
        if not isinstance(data, dict):
            raise ValueError(f"A custom payload is expected to be a dict in the form 'payload_name: {{\"foo\": \"bar\"}}. Found: {data}")
        if len(data) != 1:
            raise ValueError(f"A custom payload is expected to contain a single key representing the payload name, mapping to its value (e.g. 'location: {{\"latitude\": 42, ...}}'). Found {len(data)} keys: {data.keys()}")

        payload_name = list(data.keys())[0]
        payload_content = list(data.values())[0]

        if not isinstance(payload_content, dict):
            raise ValueError(f"Custom payloads are expected to be dictionaries. {payload_name} has value: {payload_content}")

        return CustomPayloadIntentResponse(payload_name, payload_content)

class IntentResponseDict(dict):
    """
    This is dict of Intent responses, divided by group
    (`Dict[IntentResponseGroup, List[IntentResponse]]`):

    .. code-block:: python

        IntentResponseDict({
            IntentResponseGroup.DEFAULT: [
                TextIntentResponse(choices=["An anternative", "Another alternative])
            ],
            IntentResponseGroup.RICH: [
                TextIntentResponse(choices=["Text response for Rich group"]),
                QuickRepliesIntentResponse(replies=["A reply", "Another reply"])
            ]
        })

    In addition to a standard dict, a :meth:`~IntentResponseDict.for_group`
    convenience method is provided, to select the most suitable messages for a
    given group.
    """

    def __call__(self, response_group: IntentResponseGroup=IntentResponseGroup.RICH):
        warnings.warn("prediction.fulfillment_messages(group) is deprecated, and will be "
                      "removed in 0.4. Please update your code to use "
                      "prediction.fulfillment_messages.for_group() instead", DeprecationWarning)
        return self.for_group(response_group)

    def for_group(
        self,
        response_group: IntentResponseGroup=IntentResponseGroup.RICH
    ) -> List[IntentResponse]:
        """
        Return a list of fulfillment messages that are suitable for the given
        Response Group. The following scenarios may happen:

        * :class:`language.IntentResponseGroup.DEFAULT` is requested -> Message
          in the `DEFAULT` group will be returned
        * :class:`language.IntentResponseGroup.RICH` is requested

            * `RICH` messages are defined -> `RICH` messages are returned
            * No `RICH` message is defined -> `DEFAULT` messages are returned

        If present, messages in the "rich" group will be returned:

        >>> prediction.fulfillment_messages()
        [TextIntentResponse(choices=['I like travelling too! How can I help?']),
         QuickRepliesIntentResponse(replies=['Recommend a hotel', 'Send holiday photo', 'Where the station?'])]
         
        Alternatively, I can ask for plain-text default messages:

        >>> from intents.language import IntentResponseGroup
        >>> prediction.fulfillment_messages(IntentResponseGroup.DEFAULT)
        [TextIntentResponse(choices=['Nice, I can send you holiday pictures, or recommend an hotel'])]
        
        Args:

            response_group: The Response Group to fetch responses for
        """
        if response_group == IntentResponseGroup.RICH and \
           not self.get(response_group):
            response_group = IntentResponseGroup.DEFAULT

        return self.get(response_group, [])

#
# Language Data Loader
#

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
    :const:`IntentResponseGroup.DEFAULT` group (mandatory) can only contain plain
    text responses. A :const:`IntentResponseGroup.RICH` group can provide intent
    responses that include cards, images and quick replies.

    **Slot Filling Promps** are used to solve parameters that couldn't be tagged in
    the original message. For instance a `OrderPizza` intent may have a
    `pizza_type` parameter. When User asks "I'd like a pizza" we want to fill
    the slot by asking "What type of pizza?". `slot_filling_prompts` will map
    parameters to their prompts: `{"pizza_type": ["What type of pizza?"]}`

    Args:
        example_utterance: A list of User utterances that should be associated
            with the intent
        slot_filling_prompts: A map of prompts to use when required parameters
            are missing
        responses: The Responses that Agent will send to User when the intent is
            predicted
    """
    example_utterances: List[ExampleUtterance] = field(default_factory=list)
    slot_filling_prompts: Dict[str, List[str]] = field(default_factory=dict)
    responses: Dict[IntentResponseGroup, List[IntentResponse]] = field(default_factory=list)

def intent_language_data(
    agent_cls: "intents.model.agent.AgentType",
    intent_cls: Type[Intent],
    language_code: LanguageCode=None
) -> Dict[LanguageCode, IntentLanguageData]:
    """
    Return Language Data for the given Intent.

    Args:
        agent_cls: The Agent class that registered the Intent
        intent_cls: The Intent to load language data for
        language_code: A specific language code to load. If not present, all
            available languages will be returned
    """
    if "__intent_language_data__" in intent_cls.__dict__:
        result = intent_cls.__intent_language_data__
        if language_code and language_code not in result:
            raise KeyError(f"Intent '{intent_cls}' in Agent '{agent_cls}' doesn't seem to define "
                           f"language data for language '{language_code}")
        return result
        
    try:
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

        examples = [ExampleUtterance(s, intent_cls) for s in examples_data]
        responses = _build_responses(responses_data)
        
        language_data = IntentLanguageData(
            example_utterances=examples,
            slot_filling_prompts=language_data.get('slot_filling_prompts', {}),
            responses=responses
        )

        return {language_code: language_data}
    except Exception as e:
        raise RuntimeError(f"Failed to load language data for intent {intent_cls.name} (see stacktrace above for root cause).") from e

def render_responses(intent: Intent, language_data: IntentLanguageData) -> Tuple[IntentResponseDict, str]:
    """
    Return a copy of responses in `language_data` where intent parameter references are
    replaced with their values from the given :class:`Intent` instance.

    Args:
        intent: The intent to read parameters from
        language_data: A collection of responses for the given intent
    Return:
        Intent responses, and plaintext version
    """
    result_messages: IntentResponseDict = IntentResponseDict()
    for group, response_list in language_data.responses.items():
        result_messages[group] = [r.render(intent) for r in response_list]
    rendered_plaintext = [r.random() for r in result_messages.get(IntentResponseGroup.DEFAULT, [])]
    result_plaintext = " ".join(rendered_plaintext)
    return result_messages, result_plaintext

def _build_responses(responses_data: dict):
    result = {}

    response_group: str
    responses: List[dict]
    for response_group, responses in responses_data.items():
        try:
            response_group = IntentResponseGroup(response_group)
        except ValueError as exc:
            raise NotImplementedError(f"Unsupported Response Group '{response_group}' in " +
                "'responses'. Currently, only 'default' and 'rich' are supported") from exc

        result[response_group] = []
        for r in responses:
            assert len(r) == 1
            for r_type, r_data in r.items():
                if response_group == IntentResponseGroup.DEFAULT and r_type != 'text':
                    raise ValueError(f"Message type {r_type} found in response group 'default'. " +
                        "Only 'text' type is allowed in 'default': please define the additional " +
                        "'rich' response group to use rich responses.")

                if r_type == 'text':
                    result[response_group].append(TextIntentResponse.from_yaml(r_data))
                elif r_type == 'quick_replies':
                    result[response_group].append(QuickRepliesIntentResponse.from_yaml(r_data))
                elif r_type == 'image':
                    result[response_group].append(ImageIntentResponse.from_yaml(r_data))
                elif r_type == 'card':
                    result[response_group].append(CardIntentResponse.from_yaml(r_data))
                elif r_type == 'custom':
                    result[response_group].append(CustomPayloadIntentResponse.from_yaml(r_data))
                else:
                    raise NotImplementedError(f"Unsupported response type '{r_type}'. Currently, " +
                        "only 'text' is supported")
                
    return result
