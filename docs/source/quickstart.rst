Quickstart
==========

Here some guidance on how to move the first steps with *Intents*. Here we will
show how to connect an Agent to **Dialogflow ES** to make predictions and trigger Intents.

Install
-------

.. code-block:: sh

    pip install intents

Define An Agent
---------------

The idea is to create your own Python package that will contain the whole Agent.
Let's create an **intent** in `my_agent/smalltalk.py`. 

.. code-block:: python

    from dataclasses import dataclass
    from intents import Intent, Sys

    @dataclass
    class UserSaysName(Intent):
        """My name is Mary"""
        user_name: Sys.Person

We'll define **language** resources separately in
`my_agent/language/en/smalltalk.UserSaysName.yaml` (remember your `__init__.py`
in each folder).

.. code-block:: yaml

    examples:
      - My name is $user_name{Mary}
      - Hi, I'm $user_name{Mario}

    responses:
      default:
        - text:
          - Hi $user_name, I'm Bot
          - Nice to meet you $user_name!

Finally, let's create an **Agent** in `my_agent/agent.py`, and register the
`smalltalk` module we just defined.

.. code-block:: python

    from intents import Agent
    from my_agent import smalltalk

    class MyAgent(Agent):
        """A toy Agent that still has a docstring"""

    MyAgent.register(smalltalk)

We have just defined a conversational Agent with one Intent. :ref:`Example
Agent` is a more complete example, and it's included in the library's repo
(https://github.com/dariowho/intents/tree/master/example_agent).

Setup a Dialogflow Agent
------------------------

We will operate on a real Agent on Dialogflow ES. To do this we must have access
to one, and particularly:

#. Register to Dialogflow ES
#. Create a new Agent
#. Make sure API acess is enabled 
#. Download JSON credentials for using a service account.

The whole procedure is described here:
https://cloud.google.com/dialogflow/es/docs/quick/setup.

Connect to Dialogflow
---------------------

Agents alone are abstract. To use them with Dialogflow we need a specific
**connector**:

.. code-block:: python
    
    from intents.connectors import DialogflowEsConnector
    dialogflow = DialogflowEsConnector('/path/to/your/service_account.json', MyAgent)

Upload to Cloud Agent
---------------------

Let's **upload** our example agent into our Dialogflow project:

.. code-block:: python
    
    dialogflow.upload()

This translates your Python Agent definition in Dialogflow ES format, and uploads
it into its cloud project: you will find it in your Dialogflow console at
https://dialogflow.cloud.google.com

Make predictions
----------------

We can use the same Connector as a **prediction client** for the agent you just uploaded.

.. code-block:: python

    prediction = dialogflow.predict("My name is Guido")

    prediction.intent              # UserNameGive(user_name="Guido")
    prediction.intent.user_name    # "Guido"
    prediction.fulfillment_text    # "Hi Guido, I'm Bot"
    prediction.confidence          # 0.84

Intents can also be triggered programmatically with :meth:`~intents.connectors.interface.Connector.trigger`.

Sessions
--------

We are done with *Intents* fundamentals. However, you may have noticed that we
didn't include any information about the User who is sending message. Since
(hopefully) our Agent will converse with many users, each with a different
conversation history and context, it is crucial to keep them separate and inform
the Agent about its User at prediction time.

Borrowing terminology from Dialogflow, we call each of these conversations a
**session**. Sessions can be included in prediction/trigger requests:

.. code-block:: python

    dialogflow = DialogflowEsConnector('service_account.json', ExampleAgent)
    dialogflow.predict("My name is Ada", session='user-id-ada')

The `session` string is arbitrary: it will be created if it doesn't exist on the
Cloud Agent. Session information can also be set when the Connector is created.

.. code-block:: python

    dialogflow = DialogflowEsConnector('service_account.json', ExampleAgent, default_session='user-id-bob')
    dialogflow.predict("My name is Bob")

Note that `user-id-ada` and `user-id-ada` are arbitrary strings that identifies the
current conversation. If `default_session` is omitted, a random string will be generated.

What now?
---------

Now that you know the basics, you can either:

* Dive deep into the :ref:`Core API` to learn the details of how *Intents* work.
* Explore the included :ref:`Example Agent`, that describes all the available
  features of the framework
