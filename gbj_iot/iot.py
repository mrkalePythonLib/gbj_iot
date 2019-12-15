# -*- coding: utf-8 -*-
"""Module for common constants, function, and classes for the IoT."""
__version__ = '0.1.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2019, ' + __author__
__credits__ = []
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'


# Standard library modules
import logging
from abc import ABC, abstractmethod
from enum import Enum


###############################################################################
# Enumeration and parameter classes
###############################################################################
class Status:
    """Enumeration of possible status tokens for MQTT topics."""

    (
        ONLINE, OFFLINE, ACTIVE, IDLE,
    ) = ('Online', 'Offline', 'Active', 'Idle')


class Command:
    """Enumeration of possible commands tokens for MQTT topics."""

    (
        STATUS, RESET, ON, OFF, TOGGLE,
    ) = ('STATUS', 'RESET', 'ON', 'OFF', 'TOGGLE')


class Category(Enum):
    """Enumeration of possible MQTT topic parameters."""
    STATUS = 'state'
    COMMAND = 'cmd'
    DATA = 'data'


###############################################################################
# IoT core
###############################################################################
class Plugin(object):
    """General processing for IoT devices."""

    # Predefined configuration file sections related to MQTT
    TOPIC_SEP = '/'
    """str: MQTT topic items separator."""

    def __init__(self):
        """Create the class instance - constructor."""
        # Logging
        self._logger = logging.getLogger(' '.join([__name__, __version__]))

    def __str__(self):
        """Represent instance object as a string."""
        msg = \
            f'{self.__class__.__name__}()'
        return msg

    def __repr__(self):
        """Represent instance object officially."""
        msg = \
            f'{self.__class__.__name__}()'
        return msg

    @property
    @abstractmethod
    def id(self):
        """Identifier of the pluging and the root MQTT topic fragment."""
        ...

    @property
    def logger(self):
        """Logger dedicated for the plugin."""
        return self._logger

    @property
    def mqtt_client(self):
        """MQTT client created by a main application."""
        return self._mqtt_client

    @mqtt_client.setter
    def mqtt_client(self, client: object):
        """Inject MQTT client for publishing purposes."""
        self._mqtt_client = client

    def check_category(self, category: Category) -> str:
        """Check validity of the  enumeration member and return its value."""
        try:
            if isinstance(category, Category):
                category = category.value
            else:
                category = Category[category].value
            return category
        except KeyError:
            errmsg = f'Unknown MQTT topic {category=}'
            self._logger.error(errmsg)
            raise Exception(errmsg)

    def get_topic(
        self,
        category: Category,
        parameter: str = None,
        measure: str = None) -> str:
        """Compose MQTT topic name from prescribed topic parts.

        Arguments
        ---------
        category
            Enumerated category of a MQTT topic.
        parameter
            Optional and arbitrary name of a parameter, which values is
            transmitted by the MQTT topic. It is usually a name of a physical
            unit or an operational parameter.
        measure
            Optional and arbitrary name of an aspect related to tranmitted
            value. It is usually a statistical measure like minimum, maximum,
            current value, etc.

        Returns
        -------
        str
            MQTT topic name or None in case of failure.


        """
        topic = [self.id]
        topic.append(self.check_category(category))
        # Optional topic parts
        if parameter:
            topic.append(parameter)
        if measure:
            topic.append(measure)
        # Compose topic
        topic_name = self.TOPIC_SEP.join(topic)
        return topic_name

    def begin(self):
        """Actions at starting IoT application."""
        self._logger.debug(f'Plugin "{self.id}" started')

    def finish(self):
        """Actions at finishing IoT application."""
        self._logger.debug(f'Plugin "{self.id}" stopped')

    @abstractmethod
    def publish_status(self):
        """Publish to all MQTT topics with potential parameters and measures
        typical for the plugin.
        """
        ...
