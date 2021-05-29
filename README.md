# Intents ⛺

[![Documentation Status](https://readthedocs.org/projects/intents/badge/?version=latest)](https://intents.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/dariowho/intents/branch/master/graph/badge.svg?token=XAVLW70J8S)](https://codecov.io/gh/dariowho/intents)
[![HEAD version](https://badgen.net/badge/head/v0.1.dev2/blue)](https://badgen.net/badge/head/v0.1.dev2/blue)
[![PyPI version](https://badge.fury.io/py/intents.svg)](https://badge.fury.io/py/intents)

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

*Intents* can be installed as follows:

```sh
pip install intents
```

## Usage

Intents are defined like standard Python **dataclasses**:

```python
@dataclass
class HelloIntent(Intent):
    user_name: Sys.Person = "Guido"
```

Their **language** resources are stored in separate YAML files:

```yaml
utterances:
  - Hi! My name is $user_name{Guido}
  - Hello there, I'm $user_name{Mario}

responses:
  default:
    text:
      - Hi $user_name
      - Hello $user_name
      - Nice to meet you, $user_name
```

Agents can be automatically **exported** into Cloud Dialogflow projects; *Intents* will act transparently as a prediction client:

```python
df = DialogflowEsConnector('/path/to/service-account.json', MyAgent)
predicted = df.predict("Hi there, my name is Mario")  # HelloIntent(user_name="Mario")
print(predicted.fulfillment_text)                     # "Hello Mario"
```

For a complete working example, check out the included [Example Agent](example_agent/). Also, *Intents* **documentation** is published at https://intents.readthedocs.io/ 📚

## Develop

### Setup

Dependencies are managed with Poetry
(https://python-poetry.org/docs/#installation). This is how you setup your
environment:

    poetry install

### Build Documentation

This project is documented using Sphinx. This is how you build the documentation site:

```sh
cd docs/
poetry run make html
```

Documentation will be created in the `docs/_build/` folder.

### Test

Unit tests are managed with `pytest`:

    poetry run pytest

To produce a full coverage report:

    poetry run pytest --cov=intents --cov-report xml --cov-report html
