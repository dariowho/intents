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

    def fulfill(self, context: FulfillmentContext):
        try:
            result = do_calculation(self.first_operand, self.second_operand, self.operator)
            response_intent = SolveMathOperationResponse(operation_result=result)
            return FulfillmentResult(trigger=response_intent)
        except ValueError:
            return FulfillmentResult(trigger=SolveMathOperationError)

@dataclass
class SolveMathOperationResponse(Intent):
    """
    This is triggered by :class:`SolveMathOperation` to show the result to user
    """
    # result: int = from_code()
    operation_result: Sys.Integer

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
