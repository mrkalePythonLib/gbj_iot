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
# import abc


###############################################################################
# Enumeration and parameter classes
###############################################################################
class Status:
    """Enumeration of possible status tokens for MQTT topics."""

    (
        ONLINE, OFFLINE, ACTIVE, IDLE,
    ) = range(4)


class Command:
    """Enumeration of possible commands tokens for MQTT topics."""

    (
        STATUS, RESET, ON, OFF, TOGGLE,
    ) = range(5)


# Mapping status and command codes to tokens
status_map = []
command_map = []

# Status codes
status_map.insert(Status.ONLINE, 'Online')  # Connected for LWT topic
status_map.insert(Status.OFFLINE, 'Offline')  # Disconnected for LWT topic
status_map.insert(Status.ACTIVE, 'Active')
status_map.insert(Status.IDLE, 'Idle')

# Commands
command_map.insert(Command.STATUS, 'STATUS')  # Requesting status data
command_map.insert(Command.RESET, 'RESET')  # Requesting reset of parameters
command_map.insert(Command.ON, 'ON')
command_map.insert(Command.OFF, 'OFF')
command_map.insert(Command.TOGGLE, 'TOGGLE')


# -------------------------------------------------------------------------
# Getters
# -------------------------------------------------------------------------
def status_token(index):
    """Return token value for token index."""
    try:
        token = status_map[index]
    except Exception:
        token = None
    return token


def status_index(token):
    """Return token index for token value."""
    index = None
    for i, t in enumerate(status_map):
        if t == token:
            index = i
            break
    return index


def command_token(index):
    """Return token value for token index."""
    try:
        token = command_map[index]
    except Exception:
        token = None
    return token


def command_index(token):
    """Return token index for token value."""
    index = None
    for i, t in enumerate(command_map):
        if t == token:
            index = i
            break
    return index


###############################################################################
# IoT core
###############################################################################
class IoTcore(object):
    """General processing for IoT devices."""

    def __init__(self):
        """Create the class instance - constructor."""
        # Logging
        self._logger = logging.getLogger(' '.join([__name__, __version__]))
        self._logger.debug(
            'Instance of %s created: %s',
            self.__class__.__name__, str(self)
        )

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
    def value_min(self):
        """Minimal acceptable value."""
        return self._value_min

    @value_min.setter
    def value_min(self, value):
        """Set minimal acceptable value."""
        try:
            self._value_min = float(value)
        except (TypeError, ValueError):
            self._value_min = None

    @property
    def value_max(self):
        """Maximal acceptable value."""
        return self._value_max

    @value_max.setter
    def value_max(self, value):
        """Set maximal acceptable value."""
        try:
            self._value_max = float(value)
        except (TypeError, ValueError):
            self._value_max = None

    def filter(self, value):
        """Filter value against acceptable value range.

        Arguments
        ---------
        value : float
            Value to be filtered.

        Returns
        -------
        float | None
            If the input value is outside of the acceptable value range, None
            is returned, otherwise that value.

        """
        if value is None:
            return
        if self.value_max is not None and value > self.value_max:
            self._logger.warning('Rejected value %f greater than %f',
                                 value, self.value_max)
            return
        if self.value_min is not None and value < self.value_min:
            self._logger.warning('Rejected value %f less than %f',
                                 value, self.value_min)
            return
        return value
