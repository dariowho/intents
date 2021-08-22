Intents ⛺
==========

**Intents** is a Python framework to define and operate Conversational
Agents with a simple, code-first approach. `Dialogflow ES <https://dialogflow.cloud.google.com/>`_ is the primary
supported NLU service.

Why *Intents*
=============

Define Agents as Python classes
-------------------------------
Dialogflow UI is great, but we are coders. With *Intents* your Agent is defined
**within your software** project, with native Python structures. Autocomplete and
static code checks are back, to make your Agents more flexible, scalable and
maintainable.

Versioning and Continuous Integration
-------------------------------------
With *Intents* you can **generate an Agent from code**, your developers
can work in branches, the right Agent can be generated and restored
programmatically in CI pipelines.

Human-friendly Connectors
-------------------------
Agent definitions are service-agnostic. While built-in support for **Dialogflow ES**
is provided, you are free to develop connectors for any other platform. And
since your intents are classes, predictions will just be their instances. 

Documentation Content
=====================

.. toctree::
   :maxdepth: 2

   quickstart
   STATUS.md

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/index
   connectors/index
   builtin_entities
   example_agent

.. toctree::
   :maxdepth: 2
   :caption: Developer Reference

   development


Disclaimer
==========

*This project is not affiliated, associated, authorized, endorsed by, or in any way officially connected with Dialogflow. The names Dialogflow, Google, as well as related names, marks, emblems and images are registered trademarks of their respective owners.*

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
