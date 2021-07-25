import logging
from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Any, Union, Tuple

from google.protobuf.json_format import MessageToDict
from google.cloud.dialogflow_v2.types import DetectIntentResponse

logger = logging.getLogger(__name__)

@dataclass
class DfResponseContextParameter:
    value: Union[str, dict]=None
    original: str=None

@dataclass
class DfResponseContext:
    name: str
    full_name: str
    lifespan: int
    parameters: Dict[str, DfResponseContextParameter]

class DialogflowResponse():
    
    protobuf_response: DetectIntentResponse

    def __init__(self, protobuf_response: DetectIntentResponse):
        self.protobuf_response = protobuf_response

    @property
    def intent_name(self):
        return self.protobuf_response.query_result.intent.display_name

    @property
    def intent_parameters(self):
        return MessageToDict(self.protobuf_response._pb.query_result.parameters)

    def contexts(self) -> Tuple[Dict[str, DfResponseContext], Dict[str, DfResponseContextParameter]]:
        """
        Return a "context_name -> Context" dict of the context in the given
        response, and a dict of global parameter values. In Dialogflow, parameters
        with the same name are overwritten in all contexts, even if they come from
        different intents. Because of this, we can build a map of all global names
        and their values

        TODO: cover less frequent cases (Event/context parameter source,
        event/context/constant parameter default, ...)

        :return: A dict of Contexts, A dict of global parameter values
        """
        result_contexts = {}

        for c in self.protobuf_response._pb.query_result.output_contexts:
            context_dict = MessageToDict(c)
            parameters: Dict[str, DfResponseContextParameter] = defaultdict(DfResponseContextParameter)
            for p_name, p_value in context_dict.get("parameters", {}).items():
                if p_name.endswith(".original"):
                    p_name = p_name[:-9]
                    parameters[p_name].original = p_value
                else:
                    parameters[p_name].value = p_value

            context = DfResponseContext(
                name=context_dict["name"].split('/')[-1],
                full_name=context_dict["name"],
                lifespan=context_dict["lifespanCount"],
                parameters=parameters
            )
            result_contexts[context.name] = context

        result_parameters = _build_global_context_parameters(result_contexts)

        return result_contexts, result_parameters

def _build_global_context_parameters(
    contexts: Dict[str, DfResponseContext]
) -> Dict[str, DfResponseContextParameter]:
    result = {}
    for c in contexts.values():
        for p_name, p_value in c.parameters.items():
            if p_name in result and result[p_name] != p_value:
                logger.warning("Parameter '%s' has different value in existing context. " +
                    "This may cause unexpected behavior. Current value: %s. Existing " +
                    "value: %s.", p_name, p_value, result[p_name])
            result[p_name] = p_value
    return result
