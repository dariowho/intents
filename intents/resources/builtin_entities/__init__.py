"""
Not all Services support the same set of Entities, and therefore it's not
guaranteed that all the entities in :class:`~intents.model.entity.Sys` are
available natively in all the Connectors.

Here we include some built-in custom entities that are used by Connectors for
services that don't provide native support.

.. warning::

    Most of the language content in this module was not reviewed by native
    speakers, nor it was extensively tested. It is recommended to be cautious
    when using them in production.
"""
