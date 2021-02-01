"""
Here we export a :class:`Agent` to Dialogflow format.
"""
import os
import json
import shutil
import logging
from uuid import uuid1
from typing import List
from dataclasses import asdict

from dialogflow_agents import Agent
from dialogflow_agents import language
from dialogflow_agents.model.intent import IntentMetaclass
import dialogflow_agents.dialogflow_format.agent_definition as df

logger = logging.getLogger(__name__)

def export(agent_cls: type, output_path: str) -> None:
    """
    Export the given agent to the given path
    """
    intents_path = os.path.join(output_path, 'intents')
    entities_path = os.path.join(output_path, 'entities')

    if os.path.isdir(intents_path):
        logger.warning(f"Removing existing intents folder: {intents_path}")
        shutil.rmtree(intents_path)

    if os.path.isdir(entities_path):
        logger.warning(f"Removing existing entities folder: {entities_path}")
        shutil.rmtree(entities_path)

    os.makedirs(intents_path)
    os.makedirs(entities_path)

    for intent in agent_cls.intents:
        # TODO: handle multiple languages
        examples, responses = language.intent_language_data(agent_cls, intent)
        rendered_intent = render_intent(intent, responses)
        with open(os.path.join(intents_path, f"{intent.metadata.name}.json"), "w") as f:
            json.dump(asdict(rendered_intent), f, indent=4)
        rendered_intent_usersays = render_intent_usersays(agent_cls, intent, examples)
        with open(os.path.join(intents_path, f"{intent.metadata.name}_usersays_en.json"), "w") as f:
            usersays_data = [asdict(x) for x in rendered_intent_usersays]
            json.dump(usersays_data, f, indent=4)

def render_intent(intent: IntentMetaclass, responses: List[language.ResponseUtterance]):
    response = df.Response(
        affectedContexts=[],
        parameters=[],
        messages=[],
        action=intent.metadata.action
    )

    return df.Intent(
        id=str(uuid1()),
        name=intent.metadata.name,
        responses=[response],
        webhookUsed=intent.metadata.intent_webhook_enabled,
        webhookForSlotFilling=intent.metadata.slot_filling_webhook_enabled,
        events=intent.metadata.events
    )

def render_intent_usersays(agent_cls: type, intent: IntentMetaclass, examples: List[language.ExampleUtterance]):
    result = []
    for e in examples:
        result.append(df.IntentUsersays(
            id=str(uuid1()),
            data=e.df_chunks()
        ))
    return result

from example_agent import ExampleAgent
export(ExampleAgent, '/home/dario/lavoro/dialogflow-agents/TMP_EXPORT')
