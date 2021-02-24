"""
Here we export a :class:`Agent` to Dialogflow format.
"""
import os
import json
import shutil
import logging
import tempfile
import dataclasses
from uuid import uuid1
from typing import List
from dataclasses import asdict

from dialogflow_agents import Agent
from dialogflow_agents import language
from dialogflow_agents.model.intent import _IntentMetaclass
import dialogflow_agents.dialogflow_format.agent_definition as df

logger = logging.getLogger(__name__)

def export(agent: Agent, output_path: str) -> None:
    """
    Export the given agent to the given path
    """
    assert isinstance(agent, Agent)
    agent_cls = agent.__class__

    output_dir = os.path.join(tempfile.gettempdir(), 'dialogflow-agents-export', agent.name)
    intents_dir = os.path.join(output_dir, 'intents')
    entities_dir = os.path.join(output_dir, 'entities')

    if os.path.isdir(intents_dir):
        logger.warning(f"Removing existing intents folder: {intents_dir}")
        shutil.rmtree(intents_dir)

    if os.path.isdir(entities_dir):
        logger.warning(f"Removing existing entities folder: {entities_dir}")
        shutil.rmtree(entities_dir)

    os.makedirs(intents_dir)
    os.makedirs(entities_dir)

    with open(os.path.join(output_dir, 'agent.json'), 'w') as f:
        json.dump(asdict(render_agent(agent)), f, indent=2)

    with open(os.path.join(output_dir, 'package.json'), 'w') as f:
        json.dump({"version": "1.0.0"}, f, indent=2)

    for intent in agent_cls.intents:
        # TODO: handle multiple languages
        examples, responses = language.intent_language_data(agent_cls, intent)
        rendered_intent = render_intent(intent, responses)
        with open(os.path.join(intents_dir, f"{intent.metadata.name}.json"), "w") as f:
            json.dump(asdict(rendered_intent), f, indent=2)
        rendered_intent_usersays = render_intent_usersays(agent_cls, intent, examples)
        with open(os.path.join(intents_dir, f"{intent.metadata.name}_usersays_en.json"), "w") as f:
            usersays_data = [asdict(x) for x in rendered_intent_usersays]
            json.dump(usersays_data, f, indent=2)

    if output_path.endswith('.zip'):
        output_path = output_path[:-4]
    shutil.make_archive(output_path, 'zip', output_dir)

def render_agent(agent: Agent):
    google_assistant = df.AgentGoogleAssistant(
        project=agent.gcp_project_id,
        oAuthLinking=df.AgentGoogleAssistantOauthLinking()
        # TODO: include Google Assistant configuration
    )

    webhook = df.AgentWebhook(
        # TODO: include Webhook configuration
    )

    return df.Agent(
        displayName=agent.name,
        webhook=webhook,
        googleAssistant=google_assistant
    )

def render_intent(intent: _IntentMetaclass, responses: List[language.ResponseUtterance]):
    response = df.Response(
        affectedContexts=[df.AffectedContext(c.name, c.lifespan) for c in intent.metadata.output_contexts],
        parameters=render_parameters(intent),
        messages=render_responses(intent, responses),
        action=intent.metadata.action
    )

    return df.Intent(
        id=str(uuid1()),
        name=intent.metadata.name,
        contexts=[c.name for c in intent.metadata.input_contexts],
        responses=[response],
        webhookUsed=intent.metadata.intent_webhook_enabled,
        webhookForSlotFilling=intent.metadata.slot_filling_webhook_enabled,
        events=[df.Event(e) for e in intent.metadata.events]
    )

def render_parameters(intent: _IntentMetaclass):
    result = []
    for field in intent.__dataclass_fields__.values():
        required = isinstance(field.default, dataclasses._MISSING_TYPE)
        value = f"${field.name}"
        # Could reference a context
        if field.type.df_parameter_value:
            value = field.type.df_parameter_value
        result.append(df.Parameter(
            id=str(uuid1()),
            name=field.name,
            required=required,
            dataType=f'@{field.type.df_entity.name}',
            value=value,
            defaultValue=field.default if not required else '',
            isList=False
            # TODO: support prompts
        ))
    return result

def render_responses(intent: _IntentMetaclass, responses: List[language.ResponseUtterance]):
    if not responses:
        return [df.ResponseMessage()]

    return [r.df_response() for r in responses]

def render_intent_usersays(agent_cls: type, intent: _IntentMetaclass, examples: List[language.ExampleUtterance]):
    result = []
    for e in examples:
        result.append(df.IntentUsersays(
            id=str(uuid1()),
            data=e.df_chunks()
        ))
    return result

# from example_agent import ExampleAgent
# agent = ExampleAgent('/home/dario/lavoro/dialogflow-agents/_tmp_agents/learning-dialogflow-5827a2d16c34.json')
# export(agent, '/home/dario/lavoro/dialogflow-agents/TMP_AGENT.zip')
