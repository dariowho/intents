"""
An **intent** is a categorical representation of the User intention in a single
conversation turn. For instance, utterances like "I want a pizza", "I'd like to
order a pizza" and such, could be mapped to a single `OrderPizza` intent.

Your agent will typically define a number of *intents*, representing all the
types of messages the Agent can understand and answer to. This is done by
defining :class:`Intent` sub-classes and their language resources (see
:mod:`intents.language`), and registering them to an :class:`intents.Agent`
class with :meth:`intents.Agent.register`.
"""
import inspect
import logging
import dataclasses
from dataclasses import dataclass
from typing import List, Dict, Any, _GenericAlias

from intents.model import entity, names, fulfillment
from intents.helpers.data_classes import is_dataclass_strict

logger = logging.getLogger(__name__)

#
# Intent
#

@dataclass
class IntentParameterMetadata:
    """
    Model metadata of a single Intent parameter. `IntentParameterMetadata`
    objects are built internally by :meth:`Intent.parameter_schema` based on the
    Intent dataclass fields.

    Args:
        name: Parameter name
        entity_cls: Parameter type
        is_list: Parameter will match multiple values in the User utterance
        required: If True, user will be prompted for parameter value when that
            can't be tagged in his utterance
        default: If set, this value will be used when parameter value can't be
            tagged in the User's utterance
    """
    name: str
    entity_cls: entity.EntityType
    is_list: bool
    required: bool
    default: Any

class IntentType(type):

    name: str = None

    def __new__(cls, name, bases, dct):
        result_cls = super().__new__(cls, name, bases, dct)

        # Do not process Intent base class
        if name == 'Intent':
            assert not bases
            return result_cls

        for base_cls in bases:
            if base_cls is not Intent:
                if not is_dataclass_strict(base_cls):
                    logger.warning("Intent '%s' is inheriting from non-dataclass '%s'. Did you forget the decorator?", result_cls, base_cls)

        if "name" not in result_cls.__dict__:
            result_cls.name = _intent_name_from_class(result_cls)

        names.check_name(result_cls.name)

        # TODO: check that custom parameters don't overlap Intent fields
        # TODO: check language data
        # language.intent_language_data(cls, result) # Checks that language data is existing and consistent

        return result_cls

    @property
    def parameter_schema(cls) -> Dict[str, IntentParameterMetadata]:
        """
        Return a dict representing the Intent parameter definition. A key is a
        parameter name, a value is a :class:`IntentParameterMetadata` object.

        TODO: This property doesn't show up in documentation
        """
        if cls is Intent:
            return {}

        if not is_dataclass_strict(cls):
            logger.warning(f"{cls} is not a dataclass. This may cause unexpected behavior: consider adding a @dataclass decorator to your Intent class.")
            cls = dataclass(cls)

        result = {}
        for param_field in cls.__dataclass_fields__.values():
        # for param_field in cls.__dict__['__dataclass_fields__'].values():
            # List[...]
            if inspect.isclass(param_field.type) and issubclass(param_field.type, Intent):
                continue

            if isinstance(param_field.type, _GenericAlias):
                if param_field.type.__dict__.get('_name') != 'List':
                    raise ValueError(f"Invalid typing '{param_field.type}' for parameter '{param_field.name}'. Only 'List' is supported.")

                if len(param_field.type.__dict__.get('__args__')) != 1:
                    raise ValueError(f"Invalid List modifier '{param_field.type}' for parameter '{param_field.name}'. Must define exactly one inner type (e.g. 'List[Sys.Integer]')")
                
                # From here on, check the inner type (e.g. List[Sys.Integer] -> Sys.Integer)
                entity_cls = param_field.type.__dict__.get('__args__')[0]
                is_list = True
            else:
                entity_cls = param_field.type
                is_list = False

            if not issubclass(entity_cls, entity.EntityMixin):
                raise ValueError(f"Parameter '{param_field.name}' of intent '{cls.name}' is of type '{entity_cls}', which is not an Entity.")

            required = True
            default = None
            if not isinstance(param_field.default, dataclasses._MISSING_TYPE):
                required = False
                default = param_field.default
            if not isinstance(param_field.default_factory, dataclasses._MISSING_TYPE):
                required = False
                default = param_field.default_factory()

            if not required and is_list and not isinstance(default, list):
                raise ValueError(f"List parameter has non-list default value in intent {cls}: {param_field}")

            result[param_field.name] = IntentParameterMetadata(
                name=param_field.name,
                entity_cls=entity_cls,
                is_list=is_list,
                required=required,
                default=default
            )

        return result

class Intent(metaclass=IntentType):
    """
    Represents a predicted intent. This is also used as a base class for the
    intent classes that model a Dialogflow Agent in Python code.

    In its simplest form, an Intent can be defined as follows:

    .. code-block:: python

        from intents import Intent

        class UserSaysHello(Intent):
            \"\"\"A little docstring for my Intent\"\"\"

    *Intents* will then look for language resources in the folder where your
    Agent class is defined, and specifically in
    `language/<LANGUAGE-CODE>/smalltalk.user_says_hello.yaml`. Note that the
    name of the module where the Intent is defined (`smalltalk.py`) is used as a
    prefix. More details in :mod:`intents.language`.

    Intents can be more complex than this, for instance:

    .. code-block:: python

        from dataclasses import dataclass
        from intents import Intent, Sys

        @dataclass
        class UserSaysHello(Intent):
            \"\"\"A little docstring for my Intent\"\"\"

            user_name: Sys.Person

            name = "hello_custom_name"

    This Intent has a custom name, so it will appear as "hello_custom_name" when
    exported to Dialogflow, and its language file will just be
    `hello_custom_name.yaml`, without module prefix. See
    :func:`~intents.model.names.check_name` for more details on the rules that intent names
    must follow.

    Most importantly, this intent has a `user_name` **parameter** of type
    :class:`Sys.Person` (check out :class:`intents.model.entity.Sys` for
    available system entities). With adequate examples in its language file, it
    will be able to match utterances like "Hello, my name is John", tagging
    "John" as an Entity. When a connector is instantiated, predictions will look
    like this:

    >>> predicted = connector.predict("My name is John")
    >>> predicted.intent
    user_says_hello(user_name="John")
    >>> predicted.intent.user_name
    "John"
    >>> predicted.fulfillment_text
    "Hi John, I'm Agent"

    .. warning::

        Parameter names are meant to be **unique** within an Agent. That is, the same parameter
        must always be defined with the same type. This is because 1) Some services (e.g. 
        `Alexa <https://developer.amazon.com/en-US/docs/alexa/custom-skills/create-the-interaction-model-for-your-skill.html#intent-slot-names>`_)
        require so. 2) Predictions overwrite parameters in context based on their name: better
        make sure they are compatible.

    Last, we notice the **@dataclass** decorator. We require it to be added
    explicitly, this way IDEs will recognize the Intent class as a dataclass and
    provide correct hints for names and types.
    """
    # TODO: check parameter names: no underscore, no reserved names, max length

    name: str = None

    @property
    def parameter_schema(self) -> Dict[str, IntentParameterMetadata]:
        return self.__class__.parameter_schema

    def parameter_dict(self) -> Dict[str, Any]:
        result = {}
        for parameter_name in self.parameter_schema.keys():
            result[parameter_name] = getattr(self, parameter_name)
        return result

    def fulfill(self, context: fulfillment.FulfillmentContext) -> fulfillment.FulfillmentResult:
        """
        This method defines how an Intent handles a prediction, for instance:

        .. code-block:: python

            @dataclass
            class UserConfirmsPayment(Intent):
                
                parent_order: UserOrdersSomething = follow()

                def fulfill(self, context):
                    if bank_api.check_balance() >= parent_order.amount:
                        # make payment
                        # send order
                        return FulfillmentResult(trigger=OrderSuccessResponse())
                    else:
                        return FulfillmentResponse(trigger=OrderFailedResponse())
                        
        More details about fulfillments can be found in the
        :mod:`~intents.model.fulfillment` module documentation.

        Args:
            context: Context information about the fulfillment request
                (confidence, language, ...)
        Returns:
            A `FulfillmentResult` object, that can contain a followup intent to
            trigger, or just some responses to post back to user.
        """
        return None

def _intent_name_from_class(intent_cls: IntentType) -> str:
    full_name = f"{intent_cls.__module__}.{intent_cls.__name__}"
    if intent_cls.__module__.startswith("_"):
        full_name = intent_cls.__name__
    # full_name = re.sub(r"_+", "_", full_name)
    return ".".join(full_name.split(".")[-2:])
