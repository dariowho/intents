# Dialogflow Agents

A Python library to define and operate with Dialogflow Agents with an easy,
code-first approach.

## Project status

This project is still in early development stage, its API could change without
notice. This is a broad overview of the features that are planned and their
completion status.

| Feature           | State  | Note                                                                                |
|-------------------|--------|-------------------------------------------------------------------------------------|
| [Agent Definition](STATUS.md#agent-definition)  | 🟡     | Can define basic Intents, with examples, parameters and responses                   |
| [Cloud Sync](STATUS.md#cloud-sync)        | 🟡     | Can export Agent to a valid Dialogflow ZIP. Cannot yet manage Google Cloud Projects |
| [Prediction client](STATUS.md#prediction-client) | 🟡     | Can act as a client for predictions and triggers. Cannot receive webhook requests         |

A more detailed view of the single features is reported in [STATUS.md](STATUS.md)

## Install

This library is not published anywhere yet. Wheel must be built from source, we
use Poetry (https://python-poetry.org/docs/#installation) for that:

```sh
poetry build
```

## Usage

Check out the included `example_agent/` to explore Dialogflow Agents approach to
Agent definition. In short, that is a full Agent defined as a set of Python
classes (Intents and Entities) and YAML files (language resources).

### Export Agent

A Dialogflow-compatible Agent ZIP can be built as follows:

```py
from example_agent import ExampleAgent
agent = ExampleAgent('/path/to/service_account.json')
export(agent, '/any/path/ExampleAgent.zip')
```

`ExampleAgent.zip` can be loaded into an existing Dialogflow project by using the
standard *"Settings > Export and Import > Restore from ZIP"* feature. Also via
API, if you are familiar with it.

### Predict Intent

Uploaded Agents can be accessed with a human-friendly API:

```py
from example_agent import ExampleAgent

agent = ExampleAgent('/path/to/service_account.json')
result = agent.predict("My name is Guido")

result                  # user_name_give(user_name="Guido")
result.user_name        # "Guido"
result.fulfillment_text # "Hi Guido, I'm Bot"
result.confidence       # 0.84
```

### Trigger Intent

Same goes for triggering intents:

```py
from example_agent.intents import smalltalk

agent = ExampleAgent('/path/to/service_account.json')
result = agent.trigger(smalltalk.agent_name_give(agent_name='Ugo'))

result.fulfillment_text # "Howdy Human, I'm Ugo"
```

## Documentation

tbd

## Test

tbd
