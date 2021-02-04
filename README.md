# Dialogflow Agents

A Python library to define and operate with Dialogflow Agents with an easy,
code-first approach.

## Project status

This project is still in early development stage, its API could change without
notice. This is a broad overview of the features that are planned and their
completion status.

| Feature           | State  | Note                                                                                |
|-------------------|--------|-------------------------------------------------------------------------------------|
| Agent Definition  | 🟡     | Can define basic Intents, with examples, parameters and responses                   |
| Cloud Sync        | 🟡     | Can export Agent to a valid Dialogflow ZIP. Cannot yet manage Google Cloud Projects |
| Prediction client | ❌     | Cannot act as a client for predictions, triggers and webhook requests               |

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
classes (Intents and Entities) and YAML files (language-specific resources).
Building the Dialogflow ZIP is as simple as this:

```py
from example_agent import ExampleAgent
agent = ExampleAgent('/path/to/google_application_credentials.json')
export(agent, '/any/path/ExampleAgent.zip')
```

ExampleAgent.zip can be loaded into an existing Dialogflow project by using the
standard "Settings > Export and Import > Restore from ZIP" feature. Also via
API, if you know how to use it.

Then, we want to be able to operate with the uploaded Agent with a
human-friendly Python API:

```py
from example_agent import ExampleAgent
agent = ExampleAgent('/path/to/google_application_credentials.json', session='a-new-session')
agent.predict("My name is Guido")
```

Profiding a human-friendly result:

```
user_name_give(user_name='Dario')
```

## Documentation

tbd

## Test

tbd
