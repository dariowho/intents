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

The idea is to create your own Agent Python package: it will be a requirement of
your Fulfillment project, or part of it.

For now, let's start from the :ref:`Example Agent` that is included in the
library's repo (https://github.com/dariowho/intents/tree/master/example_agent). You can use
it straight away, or explore it and adapt it at your taste.

.. code-block:: python

    from example_agent import ExampleAgent

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

Agents alone aren't tied to a particular prediction service (ideally, we can use
the same Agent on different services). To use Dialogflow we need a specific
**connector**:

.. code-block:: python
    
    from intents.connectors import DialogflowEsConnector
    dialogflow = DialogflowEsConnector('/path/to/your/service_account.json', ExampleAgent)

Upload to Cloud Agent
---------------------

Let's **upload** our example agent into our Dialogflow project:

.. code-block:: python
    
    dialogflow.upload()

This translates your Python Agent definition in Dialogflow ES format, and uploads
it into its cloud projects: you will find it in your Dialogflow console at
https://dialogflow.cloud.google.com

Make predictions
----------------

We can use the same Connector as a **prediction client** for the agent you just uploaded.

.. code-block:: python

    result = dialogflow.predict("My name is Guido")

    result                  # user_name_give(user_name="Guido")
    result.user_name        # "Guido"
    result.fulfillment_text # "Hi Guido, I'm Bot"
    result.confidence       # 0.84

Trigger Intents
---------------

Intent objects can be **instantiated**, and used to trigger intents on the Cloud
agent:

.. code-block:: python

    from example_agent import smalltalk

    result = dialogflow.trigger(smalltalk.agent_name_give(agent_name='Ugo'))

    result.fulfillment_text # "Howdy Human, I'm Ugo"
    result.confidence       # 1.0

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

* Explore the included :ref:`Example Agent`, that describes all the available
  features of the framework
* Dive deep into the :ref:`API Reference` to learn the finest details.
