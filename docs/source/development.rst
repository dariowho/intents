Development
===========

*Intents* is a standard Python project. Contributions are welcome, you can
follow the standard feature branch workflow:

#. Open an issue, or choose an existing one from https://github.com/dariowho/intents/issues
#. Open a feature branch from `develop`

   * Branch name: `"<ISSUE-NUMBER>-short-title"`

     e.g. `42-support-alexa`

   * Commit messages: `"#<ISSUE-NUMBER> Start with an imperative verb"`

     e.g. `#42 Add Alexa response schemas`

#. **rebase** frequently from develop
#. Make sure **tests** are passing
#. Open a Pull Request to develop

Setup
-----

Dependencies are managed with Poetry
(https://python-poetry.org/docs/#installation). This is how you setup your
environment:

.. code-block:: sh

    poetry install

Build Documentation
-------------------

This project is documented using Sphinx. This is how you build the documentation site:

.. code-block:: sh

    cd docs/
    poetry run make html

Documentation will be created in the `docs/_build/` folder.

Test
----

Unit tests are managed with `pytest`:

.. code-block:: sh

    poetry run pytest

To produce a full coverage report:

.. code-block:: sh

    poetry run pytest --cov=intents --cov-report xml --cov-report html
