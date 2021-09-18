"""
Here we export a :class:`Agent` to Dialogflow format.
"""
import os
import json
import shutil
import logging
import tempfile
from uuid import uuid1
from dataclasses import asdict
from typing import List, Dict, Set, Iterable, Type

from intents import Intent, EntityMixin, language
from intents.model.relations import intent_relations, FollowIntentRelation
import intents.connectors.dialogflow_es.agent_format as df
import intents.connectors.dialogflow_es.names as df_names
from intents.connectors.dialogflow_es.entities import MAPPINGS as ENTITY_MAPPINGS

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
        languages = agent_cls.languages
        json.dump(asdict(render_agent(connector, agent_name, languages)), f, indent=2)

    with open(os.path.join(output_dir, 'package.json'), 'w') as f:
        json.dump({"version": "1.0.0"}, f, indent=2)

    for intent in agent_cls.intents:
        language_data = language.intent_language_data(agent_cls, intent)
        rendered_intent = render_intent(connector, intent, language_data)
        with open(os.path.join(intents_dir, f"{intent.name}.json"), "w") as f:
            json.dump(asdict(rendered_intent), f, indent=2)
        
        for language_code, language_code_data in language_data.items():
            rendered_intent_usersays = render_intent_usersays(agent_cls, intent, language_code, language_code_data.example_utterances)
            filename = f"{intent.name}_usersays_{language_code.value}.json"
            with open(os.path.join(intents_dir, filename), "w") as f:
                usersays_data = [asdict(x) for x in rendered_intent_usersays]
                json.dump(usersays_data, f, indent=2)

    for entity_cls in agent_cls._entities_by_name.values():
        language_data = language.entity_language_data(agent_cls, entity_cls)
        rendered_entity = render_entity(entity_cls)
        with open(os.path.join(entities_dir, f"{entity_cls.name}.json"), "w") as f:
            json.dump(asdict(rendered_entity), f, indent=2)

        for language_code, entries in language_data.items():
            rendered_entity_entries = render_entity_entries(agent_cls, entries)
            filename = f"{entity_cls.name}_entries_{language_code.value}.json"
            with open(os.path.join(entities_dir, filename), "w") as f:
                entries_data = [asdict(x) for x in rendered_entity_entries]
                json.dump(entries_data, f, indent=2)

    if output_path.endswith('.zip'):
        output_path = output_path[:-4]
    shutil.make_archive(output_path, 'zip', output_dir)

#
# Agent
#

def render_agent(connector: "intents.DialogflowEsConnector",  agent_name: str, languages: List[language.LanguageCode]):
    google_assistant = df.AgentGoogleAssistant(
        project=connector.gcp_project_id,
        oAuthLinking=df.AgentGoogleAssistantOauthLinking()
        # TODO: include Google Assistant configuration
    )

    if connector.webhook_configuration:
        webhook = df.AgentWebhook(
            available=True,
            url=connector.webhook_configuration.url,
            headers=connector.webhook_configuration.headers
        )
    else:
        webhook = df.AgentWebhook()

    languages = [l.value for l in languages]
    return df.Agent(
        displayName=agent_name,
        webhook=webhook,
        googleAssistant=google_assistant,
        language=languages[0],
        supportedLanguages=languages[1:]
    )

#
# Intent
#

def get_input_contexts(connector: "DialogflowEsConnector", intent_cls: Type[Intent]) -> List[str]:
    result = [df_names.context_name(r.target_cls) for r in intent_relations(intent_cls).follow]
    
    return result

class _AffectedContextsList(list):
    """
    A list that appends a context only if no other context with the same name
    is already in the list.
    """
    added_names: Set[str]

    def __init__(self):
        super().__init__()
        self.added_names = set()

    def append(self, x: df.AffectedContext):
        if x.name in self.added_names:
            return
        self.added_names.add(x.name)
        super().append(x)

    def extend(self, x_list: List[df.AffectedContext]):
        x_list = [x for x in x_list if x.name not in self.added_names]
        for x in x_list:
            self.added_names.add(x.name)
        super().extend(x_list)

def get_output_contexts(
    connector: "DialogflowEsConnector",
    intent_cls: Type[Intent],
    visited: List[Type[Intent]]=None
) -> List[df.AffectedContext]:
    """
    An Intent can output its own context (e.g. intent `OrderFish` can spawn
    context `c_orderfish`). However, this should only happen if that context is
    actually needed (i.e. if there are intents referencing it).

    Also, this procedure is recursive: if intent `OrderFish` inherits from
    intent `OrderItem`, and there are intents referencing `c_orderitem`, then
    `OrderFish` should output `c_orderitem`
    """
    if not visited:
        visited = []

    if intent_cls is Intent:
        return []

    result = _AffectedContextsList()

    # Spawn own context if needed (i.e. at least one other intent follows this one)
    if connector._intent_needs_context(intent_cls):
        name = df_names.context_name(intent_cls)
        result.append(df.AffectedContext(name, intent_cls.lifespan))
    
    # Re-spawn context of followed intents that need to re-define lifespan
    rel: FollowIntentRelation
    for rel in intent_relations(intent_cls).follow:
        if new_lifespan := rel.relation_parameters.new_lifespan:
            for related_cls in [rel.target_cls] + rel.target_cls.parent_intents():
                context_name = df_names.context_name(related_cls)
                result.append(df.AffectedContext(context_name, new_lifespan))

    visited.append(intent_cls)
    for super_cls in intent_cls.parent_intents():
        if super_cls not in visited and issubclass(super_cls, Intent):
            result.extend(get_output_contexts(connector, super_cls, visited))

    # We cast to list because of compatibility with `asdict()`
    return list(result)

def render_intent(connector: "DialogflowEsConnector", intent_cls: Type[Intent], language_data: Dict[language.LanguageCode, language.IntentLanguageData]):
    response = df.Response(
        affectedContexts=get_output_contexts(connector, intent_cls),
        parameters=render_parameters(intent_cls, language_data),
        messages=render_responses(intent_cls, language_data, connector.rich_platforms),
    )

    return df.Intent(
        id=str(uuid1()),
        name=intent_cls.name,
        contexts=get_input_contexts(connector, intent_cls),
        responses=[response],

        # TODO: re-enable
        # webhookUsed=intent_cls.metadata.intent_webhook_enabled,
        # webhookForSlotFilling=intent_cls.metadata.slot_filling_webhook_enabled,
        events=[df.Event(df_names.event_name(intent_cls))]
    )

def render_parameters(intent_cls: Type[Intent], language_data: Dict[language.LanguageCode, language.IntentLanguageData]):
    result = []
    for param_name, param_metadata in intent_cls.parameter_schema.items():
        entity_cls = param_metadata.entity_cls
        data_type = ENTITY_MAPPINGS.service_name(entity_cls)

        prompts = []
        for language_code, language_code_data in language_data.items():
            for prompt in language_code_data.slot_filling_prompts.get(param_name, []):
                prompts.append(df.Prompt(value=prompt, lang=language_code.value))

        result.append(df.Parameter(
            id=str(uuid1()),
            name=param_name,
            required=param_metadata.required,
            dataType=f'@{data_type}',
            value=f"${param_name}",
            defaultValue=param_metadata.default if not param_metadata.required else '',
            isList=param_metadata.is_list,
            prompts=prompts
        ))
    return result

def render_response(response: language.IntentResponse, language_code: language.LanguageCode, platform: str):
    """
    platform: None = "Default"
    """
    if isinstance(response, language.TextIntentResponse):
        response: language.TextIntentResponse
        return df.TextResponseMessage(
            lang=language_code.value,
            speech=response.choices,
            platform=platform
        )
    elif isinstance(response, language.QuickRepliesIntentResponse):
        response: language.QuickRepliesIntentResponse
        return df.QuickRepliesResponseMessage(
            lang=language_code.value,
            replies=response.replies,
            platform=platform
        )
    elif isinstance(response, language.ImageIntentResponse):
        response: language.ImageIntentResponse
        return df.ImageResponseMessage(
            lang=language_code.value,
            imageUrl=response.url,
            title=response.title if response.title else "",
            platform=platform
        )
    elif isinstance(response, language.CardIntentResponse):
        response: language.CardIntentResponse
        buttons = None
        if response.link:
            buttons = [df.CardResponseMessageButton(text="👁", postback=response.link)]
        return df.CardResponseMessage(
            lang=language_code.value,
            title=response.title,
            subtitle=response.subtitle,
            imageUrl=response.image,
            buttons=buttons,
            platform=platform
        )
    elif isinstance(response, language.CustomPayloadIntentResponse):
        response: language.CustomPayloadIntentResponse
        return df.CustomPayloadResponseMessage(
            lang=language_code.value,
            payload={
                response.name: response.payload
            },
            platform=platform
        )
    else:
        raise ValueError(f"Unsupported response type: {response}")

def render_responses(intent_cls: Type[Intent], language_data: Dict[language.LanguageCode, language.IntentLanguageData], rich_platforms: Iterable[str]):
    result = []

    for language_code, language_code_data in language_data.items():
        if not language_code_data.responses:
            result.append(df.ResponseMessage(language_code.value))
            continue

        for response_group, responses in language_code_data.responses.items():
            assert response_group in [language.IntentResponseGroup.DEFAULT, language.IntentResponseGroup.RICH]
            if response_group == language.IntentResponseGroup.RICH:
                platforms_to_render = rich_platforms
            else:
                platforms_to_render = (None,) # Dialogflow will put the response in "Default" when platform=None

            for res in responses:
                for platform in platforms_to_render:
                    result.append(render_response(res, language_code, platform))

    return result

def render_utterance_chunk(chunk: language.UtteranceChunk):
    if isinstance(chunk, language.TextUtteranceChunk):
        return df.UsersaysTextChunk(text=chunk.text, userDefined=True)

    if isinstance(chunk, language.EntityUtteranceChunk):
        chunk: language.EntityUtteranceChunk
        meta = ENTITY_MAPPINGS.service_name(chunk.entity_cls)
        
        return df.UsersaysEntityChunk(
            text=chunk.parameter_value,
            alias=chunk.parameter_name,
            meta=f'@{meta}',
            userDefined=True
        )

    raise ValueError(f"Unsupported Utterance Chunk Type: {chunk}")

def render_intent_usersays(agent_cls: type, intent: Type[Intent], language_code: language.LanguageCode, examples: List[language.ExampleUtterance]):
    result = []
    for e in examples:
        result.append(df.IntentUsersays(
            id=str(uuid1()),
            lang=language_code.value,
            data=[render_utterance_chunk(c) for c in e.chunks()]
        ))
    return result

#
# Entity
#

def render_entity(entity_cls: Type[EntityMixin]) -> df.Entity:
    metadata = entity_cls.metadata
    return df.Entity(
        id=str(uuid1()),
        name=entity_cls.name,
        isRegexp=metadata.regex_entity,
        automatedExpansion=metadata.automated_expansion,
        allowFuzzyExtraction=metadata.fuzzy_matching
    )

def render_entity_entries(entity_cls: Type[EntityMixin], entries: List[language.EntityEntry]) -> List[df.EntityEntry]:
    result = []
    for e in entries:
        result.append(df.EntityEntry(
            value=e.value,
            synonyms=[e.value] + e.synonyms
        ))
    return result

