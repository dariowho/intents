# Intents ⛺

[![Documentation Status](https://readthedocs.org/projects/intents/badge/?version=latest)](https://intents.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/dariowho/intents/branch/master/graph/badge.svg?token=XAVLW70J8S)](https://codecov.io/gh/dariowho/intents)
[![HEAD version](https://img.shields.io/badge/head-v0.2.dev1-blue.svg)](https://img.shields.io/badge/head-v0.2.dev1-blue.svg)
[![PyPI version](https://badge.fury.io/py/intents.svg)](https://badge.fury.io/py/intents)

**Intents** is an unofficial Python framework to define and operate Dialogflow Agents with a simple,
code-first approach. Its main benefits are:

* **Agents are Python projects**. You will develop with autocomplete, static type checking
  and everything you are already used to.
* **Versioning and CI**. Agents can be versioned on Git, and programmatically
  deployed just like software.
* **Human-friendly prediction client**. Much more straightforward than the official
  Python SDK

A detailed view of the available features can be found in
[STATUS.md](STATUS.md). Also, check out the
[Projects](https://github.com/dariowho/intents/projects) page to keep track of
recent developments.

## Install

```sh
pip install intents
```

## Usage

Intents are defined like standard Python **dataclasses**:

```python
@dataclass
class HelloIntent(Intent):
    """A little docstring for my Intent class"""
    user_name: Sys.Person = "Guido"
MyAgent.register(HelloIntent)
```

Their **language** resources are stored in separate YAML files:

```yaml
utterances:
  - Hi! My name is $user_name{Guido}
  - Hello there, I'm $user_name{Mario}

responses:
  default:
    - text:
      - Hi $user_name
      - Hello $user_name, this is Bot!
      - Nice to meet you, $user_name
```

Agents can be **uploaded** as Dialogflow ES projects directly from code:

```python
df = DialogflowEsConnector('/path/to/service-account.json', MyAgent)
df.upload()  # You will find it in your Dialogflow Console
```

*Intents* will act transparently as a **prediction** client:

```python
>>> predicted = df.predict("Hi there, my name is Mario")
HelloIntent(user_name="Mario")
>>> predicted.fulfillment_text
"Hello Mario, this is Bot!"
>>> predicted.user_name
"Mario"
```

For a complete working example, check out the included [Example Agent](example_agent/). Also, *Intents* **documentation** is published at https://intents.readthedocs.io/ 📚

## Disclaimer

*This project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Dialogflow. The names Dialogflow, Google, as well as related names, marks, emblems and images are registered trademarks of their respective owners.*
