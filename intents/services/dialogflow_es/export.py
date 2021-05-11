"""
Here we export a :class:`Agent` to Dialogflow format.
"""
import os
import json
import shutil
import logging
import tempfile
from uuid import uuid1
from typing import List, Dict
from dataclasses import asdict

from intents import language
from intents.model.intent import _IntentMetaclass
from intents.model.entity import SystemEntityMixin, _EntityMetaclass
import intents.services.dialogflow_es.df_format as df
from intents.services.dialogflow_es.entities import MAPPINGS as ENTITY_MAPPINGS

logger = logging.getLogger(__name__)

def export(connector: "intents.DialogflowEsConnector", output_path: str, agent_name="py-agent") -> None:
    """
    Export the given agent to the given path
    """
    agent_cls = connector.agent_cls

    output_dir = os.path.join(tempfile.gettempdir(), 'dialogflow-agents-export', agent_name)
    intents_dir = os.path.join(output_dir, 'intents')
    entities_dir = os.path.join(output_dir, 'entities')

    if os.path.isdir(intents_dir):
        logger.warning("Removing existing intents folder: %s", intents_dir)
        shutil.rmtree(intents_dir)

    if os.path.isdir(entities_dir):
        logger.warning("Removing existing entities folder: %s", entities_dir)
        shutil.rmtree(entities_dir)

    os.makedirs(intents_dir)
    os.makedirs(entities_dir)

    with open(os.path.join(output_dir, 'agent.json'), 'w') as f:
        json.dump(asdict(render_agent(connector, agent_name)), f, indent=2)

    with open(os.path.join(output_dir, 'package.json'), 'w') as f:
        json.dump({"version": "1.0.0"}, f, indent=2)

    for intent in agent_cls.intents:
        # TODO: handle multiple languages
        language_data = language.intent_language_data(agent_cls, intent)
        rendered_intent = render_intent(intent, language_data)
        with open(os.path.join(intents_dir, f"{intent.metadata.name}.json"), "w") as f:
            json.dump(asdict(rendered_intent), f, indent=2)
        rendered_intent_usersays = render_intent_usersays(agent_cls, intent, language_data.example_utterances)
        with open(os.path.join(intents_dir, f"{intent.metadata.name}_usersays_en.json"), "w") as f:
            usersays_data = [asdict(x) for x in rendered_intent_usersays]
            json.dump(usersays_data, f, indent=2)

    for entity_cls in agent_cls._entities_by_name.values():
        entries = language.entity_language_data(agent_cls, entity_cls)
        rendered_entity = render_entity(entity_cls)
        with open(os.path.join(entities_dir, f"{entity_cls.name}.json"), "w") as f:
            json.dump(asdict(rendered_entity), f, indent=2)
        rendered_entity_entries = render_entity_entries(agent_cls, entries)
        with open(os.path.join(entities_dir, f"{entity_cls.name}_entries_en.json"), "w") as f:
            entries_data = [asdict(x) for x in rendered_entity_entries]
            json.dump(entries_data, f, indent=2)

    if output_path.endswith('.zip'):
        output_path = output_path[:-4]
    shutil.make_archive(output_path, 'zip', output_dir)

#
# Agent
#

def render_agent(connector: "intents.DialogflowEsConnector",  agent_name: str):
    google_assistant = df.AgentGoogleAssistant(
        project=connector.gcp_project_id,
        oAuthLinking=df.AgentGoogleAssistantOauthLinking()
        # TODO: include Google Assistant configuration
    )

    webhook = df.AgentWebhook(
        # TODO: include Webhook configuration
    )

    return df.Agent(
        displayName=agent_name,
        webhook=webhook,
        googleAssistant=google_assistant
    )

#
# Intent
#

def render_intent(intent_cls: _IntentMetaclass, language_data: language.IntentLanguageData):
    response = df.Response(
        affectedContexts=[df.AffectedContext(c.name, c.lifespan) for c in intent_cls.metadata.output_contexts],
        parameters=render_parameters(intent_cls, language_data.slot_filling_prompts),
        messages=render_responses(intent_cls, language_data.responses),
        action=intent_cls.metadata.action
    )

    return df.Intent(
        id=str(uuid1()),
        name=intent_cls.metadata.name,
        contexts=[c.name for c in intent_cls.metadata.input_contexts],
        responses=[response],
        webhookUsed=intent_cls.metadata.intent_webhook_enabled,
        webhookForSlotFilling=intent_cls.metadata.slot_filling_webhook_enabled,
        events=[df.Event(e) for e in intent_cls.metadata.events]
    )

def render_parameters(intent_cls: _IntentMetaclass, slot_filling_prompts: Dict[str, List[str]]):
    result = []
    for param_name, param_metadata in intent_cls.parameter_schema().items():
        entity_cls = param_metadata.entity_cls
        if issubclass(entity_cls, SystemEntityMixin):
            data_type = ENTITY_MAPPINGS[entity_cls].service_name
        else:
            data_type = entity_cls.name

        result.append(df.Parameter(
            id=str(uuid1()),
            name=param_name,
            required=param_metadata.required,
            dataType=f'@{data_type}',
            value=f"${param_name}",
            defaultValue=param_metadata.default if not param_metadata.required else '',
            isList=param_metadata.is_list,
            prompts=[df.Prompt(value=p) for p in slot_filling_prompts.get(param_name, {})]
        ))
    return result

def render_response(response: language.ResponseUtterance):
    if isinstance(response, language.TextResponseUtterance):
        response: language.TextResponseUtterance
        return df.TextResponseMessage(
            speech=response.choices
        )

def render_responses(intent_cls: _IntentMetaclass, responses: List[language.ResponseUtterance]):
    if not responses:
        return [df.ResponseMessage()]

    return [render_response(r) for r in responses]

def render_utterance_chunk(chunk: language.UtteranceChunk):
    if isinstance(chunk, language.TextUtteranceChunk):
        return df.UsersaysTextChunk(text=chunk.text, userDefined=True)

    if isinstance(chunk, language.EntityUtteranceChunk):
        chunk: language.EntityUtteranceChunk
        if issubclass(chunk.entity_cls, SystemEntityMixin):
            meta = ENTITY_MAPPINGS[chunk.entity_cls].service_name
        else:
            meta = chunk.entity_cls.name

        return df.UsersaysEntityChunk(
            text=chunk.parameter_value,
            alias=chunk.parameter_name,
            meta=f'@{meta}',
            userDefined=True
        )

    raise ValueError(f"Unsupported Utterance Chunk Type: {chunk}")

def render_intent_usersays(agent_cls: type, intent: _IntentMetaclass, examples: List[language.ExampleUtterance]):
    result = []
    for e in examples:
        result.append(df.IntentUsersays(
            id=str(uuid1()),
            data=[render_utterance_chunk(c) for c in e.chunks()]
        ))
    return result

#
# Entity
#

def render_entity(entity_cls: _EntityMetaclass) -> df.Entity:
    metadata = entity_cls.metadata
    return df.Entity(
        id=str(uuid1()),
        name=entity_cls.name,
        isRegexp=metadata.regex_entity,
        automatedExpansion=metadata.automated_expansion,
        allowFuzzyExtraction=metadata.fuzzy_matching
    )

def render_entity_entries(entity_cls: _EntityMetaclass, entries: List[language.EntityEntry]) -> List[df.EntityEntry]:
    result = []
    for e in entries:
        result.append(df.EntityEntry(
            value=e.value,
            synonyms=e.synonyms
        ))
    return result

# from example_agent import ExampleAgent
# agent = ExampleAgent('/home/dario/lavoro/dialogflow-agents/_tmp_agents/learning-dialogflow-5827a2d16c34.json')
# export(agent, '/home/dario/lavoro/dialogflow-agents/TMP_AGENT.zip')
