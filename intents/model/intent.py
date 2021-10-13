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
from __future__ import annotations

import inspect
import logging
import dataclasses
from dataclasses import dataclass, replace, fields
from typing import List, Dict, Union, Any, Type, T, _GenericAlias

# pylint: disable=unused-import # needed for docs
import intents
from intents import LanguageCode
from intents.model import entity, names
from intents.model.parameter import IntentParameter, SessionIntentParameter, NluIntentParameter, ParameterSchema
from intents.helpers.data_classes import is_dataclass_strict, to_dict

logger = logging.getLogger(__name__)

#
# Intent Fulfillment Structures
#

@dataclass
class FulfillmentSession:
    """
    This models information about the current session that is returned in
    :class:`FulfillmentContext` objects.
    """
    id: str

@dataclass
class FulfillmentContext:
    """
    `FulfillmentContext` objects are produced by Connectors and are input
    arguments to :meth:`Intent.fulfill`.
    """
    session: FulfillmentSession
    confidence: float
    fulfillment_text: str
    fulfillment_messages: intents.language.intent_language.IntentResponseDict
    language: LanguageCode

@dataclass
class FulfillmentResult:
    """
    `FulfillmentResult` are produced by `Intent.fulfill`, and then converted by
    Connectors into Service-actionable responses.

    .. note::

        At the moment this class is only used internally. It is safe to return
        simple :class:`Intent` instances in :meth:`Intent.fulfill`
    """
    trigger: Intent = None
    fulfillment_text: List[str] = None
    fulfillment_messages: List["intents.language.intent_language.IntentResponse"] = None
    
    @staticmethod
    def ensure(fulfill_return_value: Union[FulfillmentResult, Intent]) -> FulfillmentResult:
        """
        Convert the given object to a :class:`FulfillmentResult` instance, if it
        is not already one.

        Args:
            fulfill_return_value: An object, as it is returned by :meth:`Intent.fulfill`

        Raises:
            ValueError: If input object is not a valid return value for :meth:`Intent.fulfill`

        Returns:
            FulfillmentResult: A `FulfillmentResult` object representing input
        """
        if fulfill_return_value is None:
            return

        if isinstance(fulfill_return_value, FulfillmentResult):
            return fulfill_return_value

        if isinstance(fulfill_return_value, Intent):
            return FulfillmentResult(trigger=fulfill_return_value)

        raise ValueError(f"Unsupported fulfillment return value: {fulfill_return_value}")

#
# Intent
#

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
                if issubclass(base_cls, Intent) and not is_dataclass_strict(base_cls):
                    logger.warning("Intent '%s' is inheriting from non-dataclass '%s'. Did you forget the decorator?", result_cls, base_cls)

        if "name" not in result_cls.__dict__:
            result_cls.name = _intent_name_from_class(result_cls)

        names.check_name(result_cls.name)

        # TODO: check that custom parameters don't overlap Intent fields

        return result_cls

    @property
    def parameter_schema(cls) -> ParameterSchema:
        if cls is Intent:
            return {}

        if not is_dataclass_strict(cls):
            logger.warning("%s is not a dataclass. This may cause unexpected behavior: consider "
                           "adding a @dataclass decorator to your Intent class.", cls)
            cls = dataclass(cls)

        result = {}
        for param_field in fields(cls):
            if inspect.isclass(param_field.type) and issubclass(param_field.type, Intent):
                continue

            exc_nlu = None
            exc_session = None
            try:
                result[param_field.name] = NluIntentParameter.from_dataclass_field(param_field)
                continue
            except ValueError as exc:
                exc_nlu = exc

            try:
                result[param_field.name] = SessionIntentParameter.from_dataclass_field(param_field)
                continue
            except ValueError as exc:
                exc_session = exc

            if exc_nlu and exc_session:
                raise ValueError(f"Parameter {param_field.name} of intent {cls} cannot be "
                                 f"processed neither as a NLU Parameter ({exc_nlu}) or as a "
                                 f"Session Parameter ({exc_session})")

        return ParameterSchema(result)

class Intent(metaclass=IntentType):
    """
    This is a base class for user defined intents, which are the fundamental
    building blocks of your Agent.

    In its simplest form, an Intent can be defined as follows:

    .. code-block:: python

        from intents import Intent

        class UserSaysHello(Intent):
            \"\"\"A little docstring for my Intent\"\"\"

    *Intents* will then look for language resources in the folder where your
    Agent class is defined, and specifically in
    `language/<LANGUAGE-CODE>/smalltalk.UserSaysHello.yaml`. Note that the
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
            lifespan = 10

    This Intent has a **custom name**, so it will appear as "hello_custom_name" when
    exported to prediction services such as Dialogflow, and its language file
    will just be `hello_custom_name.yaml`, without module prefix. See
    :func:`~intents.model.names.check_name` for more details on the rules that
    intent names must follow.

    This intent has a **lifespan** member. This is used in
    :mod:`intents.model.relations` to determine how long should the Intent stay
    in the conversation context after it is predicted.

    Most importantly, this intent has a `user_name` **parameter** of type
    :class:`Sys.Person` (check out :class:`intents.model.entity.Sys` for
    available system entities). With adequate examples in its language file, it
    will be able to match utterances like "Hello, my name is John", tagging
    "John" as an Entity. When a connector is instantiated, predictions will look
    like this:

    >>> predicted = connector.predict("My name is John")
    >>> predicted.intent
    UserSaysHello(user_name="John")
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
    lifespan: int = 5

    @property
    def parameter_schema(self) -> ParameterSchema:
        """
        Return a :class:`ParameterSchema` object that represens the Intent
        parameter definition.

        TODO: this doesn't show up in docs
        """
        return self.__class__.parameter_schema

    def parameter_dict(self) -> Dict[str, IntentParameter]:
        """
        Return the Intent parameters and their values as a dict.

        Returns:
            A dict of parameters
        """
        result = {}
        for parameter_name in self.parameter_schema.keys():
            result[parameter_name] = getattr(self, parameter_name)
        return result

    @classmethod
    def parent_intents(cls) -> List[Type[Intent]]:
        """
        Return a list of the Intent parent classes. This wraps `cls.mro()`
        filtering out non-Intent parents (e.g. :class:`object`), :class:`Intent`
        and `cls` itself.

        >>> AskEspresso.parent_intents()
        [AskCoffee, AskDrink]

        Returns:
            A list of parent Intent classes
        """
        result = []
        for c in cls.mro():
            if issubclass(c, Intent) and c is not Intent and c is not cls:
                result.append(c)
        return result

    def replace(self, *, lifespan: int=None, **kwargs) -> T:
        """
        Return a copy of the given intent object replacing the given field values

        >>> OrderPizza(pizza_type="margherita").replace(lifespan=3, pizza_type="marinara")
        OrderPizza(pizza_type="marinara")

        This method is meant for **internal use**. Changing lifespans and
        parameters will most likely have an impact on session and contexts that
        have to be dealt with separately.

        Args:
            lifespan (int, optional): Intent lifespan. Defaults to None.
        Return:
            An Intent of the same type, with updated fields
        """
        if not is_dataclass_strict(self):
            logger.warning("%s is not a dataclass instance. This may cause unexpected behavior: consider "
                           "adding a @dataclass decorator to your Intent class.", self)
            self = dataclass(self)

        result = replace(self, **kwargs)
        result.lifespan = lifespan if lifespan else self.lifespan

        return result

    def fulfill(self,
        context: FulfillmentContext,
        **kwargs
    ) -> Intent:
        """
        Override this method to define a custom procedure that will be invoked
        when the Intent is predicted, possibly triggering another intent as a
        result. For instance:

        .. code-block:: python

            @dataclass
            class UserConfirmsPayment(Intent):
                
                parent_order: UserOrdersSomething = follow()

                def fulfill(self, context):
                    if shop_api.is_item_available(parent_order.item_id):
                        shop_api.make_order(parent_order.item_id)
                        return OrderSuccessResponse()
                    else:
                        return OrderFailedResponse()
                        
        In the example, when `UserConfirmsPayment` is predicted, it will run
        some business logic, and choose a different response depending on the
        result. Note that response objects are full-fledged Intents, and even
        though they probably won't include example utterances, they can
        define parameters, relations, and their own :meth:`fulfillment`
        implementation, that will be executed recursively.

        More details about fulfillments can be found in the
        :mod:`~intents.fulfillment` module documentation.

        Args:
            context: Context information about the fulfillment request
                (confidence, language, ...)
        Returns:
            A `FulfillmentResult` object, that can contain a followup intent to
            trigger, or just some responses to post back to user.
        """
        return None

def _intent_name_from_class(intent_cls: Type[Intent]) -> str:
    full_name = f"{intent_cls.__module__}.{intent_cls.__name__}"
    if intent_cls.__module__.startswith("_"):
        full_name = intent_cls.__name__
    # full_name = re.sub(r"_+", "_", full_name)
    return ".".join(full_name.split(".")[-2:])
