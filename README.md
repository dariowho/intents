# Intents ⛺

**Intents** is a Python library to define and operate Dialogflow Agents with a simple,
code-first approach.

> **disclaimer**: this project is not affiliated, associated, authorized,
> endorsed by, or in any way officially connected with Dialogflow. The names
> Dialogflow, Google, as well as related names, marks, emblems and images are
> registered trademarks of their respective owners.

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

*Intents* can be installed with PIP as a standard Python package

```sh
pip install intents
```

## Usage

Check out the included `example_agent/` to explore *Intents* approach to
Agent definition. In short, that is a full Agent defined as a set of Python
classes (Intents and Entities) and YAML files (language resources).

### Export Agent

A Dialogflow-compatible Agent ZIP can be built as follows:

```py
from example_agent import ExampleAgent
from intents.dialogflow_service.export import export

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
from example_agent import smalltalk

agent = ExampleAgent('/path/to/service_account.json')
result = agent.trigger(smalltalk.agent_name_give(agent_name='Ugo'))

result.fulfillment_text # "Howdy Human, I'm Ugo"
```

## Develop

## Setup

Dependencies are managed with Poetry
(https://python-poetry.org/docs/#installation). This is how you setup your
environment:

    poetry install

## Build Documentation

This project is documented using Sphinx. This is how you build the documentation site:

```sh
cd docs/
poetry run make html
```

Documentation will be created in the `docs/_build/` folder.

## Test

tbd
