"""
These are system entity types that are provided by Dialogflow. They are used in
intent definition.

Example:

.. code-block::python

    from dialogflow_agents.system_entities import sys

    @MyAgent.intent("example_intent")
    class ExampleIntent(Intent):

        user_name: sys.person

"""
from dialogflow_agents import Entity
from dialogflow_agents.model.entity import SystemEntity

class sys:

    any = SystemEntity(name='sys.any')
    place_attraction_us = SystemEntity(name='sys.place-attraction-us')
    given_name = SystemEntity(name='sys.given-name')
    geo_city_gb = SystemEntity(name='sys.geo-city-gb')
    geo_county_gb = SystemEntity(name='sys.geo-county-gb')
    ordinal = SystemEntity(name='sys.ordinal')
    currency_name = SystemEntity(name='currency_name')
    person = SystemEntity(name='sys.person')
    date_period = SystemEntity(name='sys.date-period')
    number = SystemEntity(name='sys.number')
    unit_weight_name = SystemEntity(name='sys.unit-weight-name')
    temperature = SystemEntity(name='sys.temperature')
    geo_state_gb = SystemEntity(name='sys.geo-state-gb')
    duration = SystemEntity(name='sys.duration')
    geo_city = SystemEntity(name='sys.geo-city')
    unit_information = SystemEntity(name='sys.unit-information')
    geo_state_us = SystemEntity(name='sys.geo-state-us')
    date_time = SystemEntity(name='sys.date-time')
    percentage = SystemEntity(name='sys.percentage')
    unit_speed_name = SystemEntity(name='sys.unit-speed-name')
    location = SystemEntity(name='sys.location')

    # TODO: complete

