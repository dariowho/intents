"""
This module demonstrates fulfillment in action, by defining a simple calculator
app. Here most of the responses cannot be defined in language files, because
they are computed from intent parameters
"""
from dataclasses import dataclass

from intents import Intent, Entity, Sys, FulfillmentContext, FulfillmentResult

class CalculatorOperator(Entity):
    """
    These are simple math operators:

    * "+", "plus"
    * "-", "minus"
    * "*", "multiplied by", "times"
    * "/", "divided by", "over"
    """

@dataclass
class SolveMathOperation(Intent):
    """
    | U: How much is 21 times two?
    | A: That's 42
    """
    first_operand: Sys.Integer
    second_operand: Sys.Integer
    operator: CalculatorOperator

    def fulfill(self, context: FulfillmentContext) -> Intent:
        """
        Compute the requested operation and sends the response back by
        triggering :class:`SolveMathOperationResponse`. If an error occurs while
        solving the operation (e.g. a division by zero),
        :class:`SolveMathOperationError` will be returned instead.

        See :meth:`intents.model.intent.Intent.fulfill` for more details about
        this method. 

        Args:
            context (FulfillmentContext): The fulfillment context, as it is
            passed by the Connector

        Returns:
            Intent: The Intent to trigger in response to the fulfillment
        """
        try:
            result = do_calculation(self.first_operand, self.second_operand, self.operator)
            return SolveMathOperationResponse(operation_result=result)
        except (ValueError, ZeroDivisionError):
            return SolveMathOperationError()

@dataclass
class SolveMathOperationResponse(Intent):
    """
    This is triggered by :class:`SolveMathOperation` to show the result to user.
    Note that this intent has a Session Parameter `operation_result` of type
    :class:`float`. Session parameters are injected by software components; they
    are less constrained than NLU Parameters, but cannot be tagged in user
    utterances, therefore the only way to fire this intent is with a trigger (in
    our case, the result of :meth:`SolveMathOperation.fulfill`). 
    """
    operation_result: float

@dataclass
class SolveMathOperationError(Intent):
    """
    This is triggered by fulfillment if something goes wrong in calculations.
    """

def do_calculation(first_operand: int, second_operand: int, operator: str):
    """
    This is a helper function that solves a simple math operation

    >>> do_calculation(2, 3, "+")
    5
    """
    if operator == "+":
        return first_operand + second_operand
    elif operator == "-":
        return first_operand - second_operand
    elif operator == "*":
        return first_operand * second_operand
    elif operator == "/":
        return first_operand / second_operand

    raise ValueError(f"Unsupported operator: {operator}")
