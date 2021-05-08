Quickstart
==========

Here some guidance on how to move the first steps with *Intents*.

Install
-------

This library is not published on PyPi yet: you must **install from source**. Make
sure you have Poetry installed (https://python-poetry.org/docs/#installation),
then install with

.. code-block:: sh

    git clone https://github.com/dario-chiappetta/dialogflow-agents.git
    cd dialogflow-agents
    poetry install

Define An Agent
---------------

The idea is to create your own Agent Python package: it will be a requirement of
your Fulfillment project, or part of it.

For now, let's start from the **example agent** that comes with the library
(`example_agent/`). You can use it straight away, or explore it and adapt it at
your taste.

.. code-block:: python

    from example_agent import ExampleAgent

Upload to Cloud Agent
---------------------

Now, **setup** a Dialogflow agent, make sure API access is enabled and that you
have JSON credentials for using a service account. The whole procedure is
described here: https://cloud.google.com/dialogflow/es/docs/quick/setup.

Once you have your Cloud agent, let's export our example agent into a Dialogflow
ZIP file:

.. code-block:: python

    from example_agent import ExampleAgent

    agent = ExampleAgent('/path/to/your/service_account.json')
    export(agent, '/anywhere/you/like/EXPORTED_EXAMPLE_AGENT.zip')

All is left to do, is to **restore** the Agent from your Dialogflow UI
(*Settings > Export and Import*). And it's done: your Python Agent definition is
translated into a working Dialogflow Agent.

Make predictions
----------------

Your `ExampleAgent` class can also be used as a **prediction client** for the agent you just uploaded.

.. code-block:: python

    from example_agent import ExampleAgent

    agent = ExampleAgent('/path/to/service_account.json', session='any-session-id')
    result = agent.predict("My name is Guido")

    result                  # user_name_give(user_name="Guido")
    result.user_name        # "Guido"
    result.fulfillment_text # "Hi Guido, I'm Bot"
    result.confidence       # 0.84

Note that `any-session-id` is a string of your choice that identifies the
current conversation. If you omit the parameter, it will be generated randomly.

Trigger Intents
---------------

Intent objects can be **instantiated**, and used to trigger intents on the Cloud
agent:

.. code-block:: python

    from example_agent import smalltalk

    agent = ExampleAgent('/path/to/service_account.json')
    result = agent.trigger(smalltalk.agent_name_give(agent_name='Ugo'))

    result.fulfillment_text # "Howdy Human, I'm Ugo"
