**Dialogflow Agents** is a framework to define and operate Dialogflow Agents
with an elegant, code-first approach. This is an overview of its features.

Define Agents as Python classes
===============================

Dialogflow UI is great, but we are coders. With *Dialogflow Agents* your Agent lives **within your software** project:
autocomplete, type hints and static code checks are back!

.. code-block:: python

   @MyAgent.intent('smalltalk.user_name.give')
   class user_gives_name(Intent):
      """
      Why not documenting my Agent Intents?
      """
      name: df_sys.person()

Versioning and Continuous Integration
=====================================
With Dialogflow Agents you can **generate an Agent from code**, your developers
can work in branches, the right Agent can be generated and restored
automatically in your CI pipelines.

A Human-friendly prediction client
==================================
The official Dialogflow Python client is not the most enjoyable piece of
sowftware you will experience as a developer. It gives you full control over the
Agent, but if you are simply interested in making
predictions and triggers, why not **keep it simple**?

.. code-block:: python

   agent = ExampleAgent('/path/to/service_account.json')
   result = agent.predict("My name is Guido")
   result.fulfillment_text # "Hi Guido, I'm Bot"

Documentation Content
=====================

.. toctree::
   :maxdepth: 2

   quickstart
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
