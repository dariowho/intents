from intents.testing import TestingStory

from example_agent.calculator import SolveMathOperation, SolveMathOperationError, SolveMathOperationResponse

def test_calculator_solve_operation(story: TestingStory):
    story.step("How much is 4 divided by 2", SolveMathOperationResponse(2), SolveMathOperation(4, 2, "/"))
    story.step("How much is 3 divided by 0", SolveMathOperationError(), SolveMathOperation(3, 0, "/"))
