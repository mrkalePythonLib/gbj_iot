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
from enum import Enum, auto
from dataclasses import dataclass


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


class Parameter(Enum):
    """Enumeration of expected MQTT topic parameters."""
    ...


class Measure(Enum):
    """Enumeration of possible MQTT topi measures."""
    VALUE = 'val'
    MINIMUM = 'min'
    MAXIMUM = 'max'
    AVERAGE = 'avg'
    PERCENTILE = 'ptl'
    PERCENTAGE = 'perc'


###############################################################################
# IoT core
###############################################################################
@dataclass
class PluginParam:
    """Plugin parameter record definition."""
    parameter: str
    measure: Measure = None
    value: any = None


class Plugin(ABC):
    """General processing for IoT devices."""

    # Predefined configuration file sections related to MQTT
    TOPIC_SEP = '/'
    """str: MQTT topic items separator."""

    def __init__(self):
        """Create the class instance - constructor."""
        self.mqtt_client = None
        # Private attributes
        self._params: [PluginParam] = []
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

    def check_category(self, category: Category) -> str:
        """Check validity of the category enumeration member and return
        its value.

        Returns
        -------
            Category name for MQTT topic.

        Raises
        -------
        ValueError
            Input string is not an enumeration key.

        """
        try:
            if isinstance(category, Category):
                category = category.value
            else:
                category = Category[category].value
            return category
        except KeyError:
            errmsg = f'Unknown MQTT topic {category=}'
            self._logger.error(errmsg)
            raise ValueError(errmsg)

    def check_parameter(self, parameter: Parameter) -> str:
        """Check validity of the parameter enumeration member and return
        its value.

        Returns
        -------
            Parameter name for MQTT topic.

        Raises
        -------
        ValueError
            Input string is not an enumeration key.

        """
        try:
            if isinstance(parameter, Parameter):
                parameter = parameter.value
            else:
                parameter = Parameter[parameter].value
            return parameter
        except KeyError:
            errmsg = f'Unknown MQTT topic {parameter=}'
            self._logger.error(errmsg)
            raise ValueError(errmsg)

    def check_measure(self, measure: Measure) -> str:
        """Check validity of the measure enumeration member and return
        its value.

        Returns
        -------
            Measure name for MQTT topic.

        Raises
        -------
        ValueError
            Input string is not an enumeration key.

        """
        try:
            if isinstance(measure, Measure):
                measure = measure.value
            else:
                measure = Measure[measure].value
            return measure
        except KeyError:
            errmsg = f'Unknown MQTT topic {measure=}'
            self._logger.error(errmsg)
            raise ValueError(errmsg)

    def get_topic(
        self,
        category: Category,
        parameter: str = None,
        measure: Measure = None) -> str:
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
            Optional enumerated measure of an aspect related to tranmitted
            value. It is usually a statistical measure like minimum, maximum,
            current value, etc.

        """
        topic = [self.id]
        topic.append(self.check_category(category))
        # Optional topic parts
        if parameter:
            topic.append(self.check_parameter(parameter))
        if measure:
            topic.append(self.check_measure(measure))
        # Compose topic
        topic_name = self.TOPIC_SEP.join(topic)
        return topic_name

    @property
    def device_topic(self) -> str:
        """Compose MQTT topic name for device identifier."""
        topic = [self.id]
        topic.append('#')
        return self.TOPIC_SEP.join(topic)

    @abstractmethod
    def begin(self):
        """Actions at starting IoT application."""
        self._logger.debug(f'Plugin "{self.id}" started')

    @abstractmethod
    def finish(self):
        """Actions at finishing IoT application."""
        self._logger.debug(f'Plugin "{self.id}" stopped')

    @abstractmethod
    def publish_status(self):
        """Publish to all MQTT topics with potential parameters and measures
        typical for the plugin.
        """
        ...

###############################################################################
# Parameters actions
###############################################################################
    def _find_param(self, parameter: Parameter, measure: Measure) -> int:
        """Find parameter in the device's parameters list.

        Arguments
        ---------
        parameter
            Enumerated parameter to be found.
        measure
            Enumerated measure to be found.

        Returns
        -------
            Index of found parameter to the list of parameters.

        Raises
        -------
        ValueError
            Parameter not found or given unknown measure.

        """
        if parameter is not None:
            _ = self.check_parameter(parameter)
        if measure is not None:
            _ = self.check_measure(measure)
        for index, param in enumerate(self._params):
            if parameter == param.parameter \
            and (measure is None or measure == param.measure):
                return index
        raise ValueError

    def get_param(self, parameter: Parameter, measure: Measure) -> any:
        """Get parameter value from the device's parameters list.

        Arguments
        ---------
        parameter
            Enumerated parameter to be found.
        measure
            Enumerated measure to be found.

        Returns
        -------
            Value of a parameter or None.

        Raises
        -------
        ValueError
            Parameter not found or given unknown measure.

        """
        result = None
        try:
            index = self._find_param(parameter, measure)
        except ValueError as errmsg:
            self._logger.error(errmsg)
        else:
            result = self._params[index].value
        return result

    def set_param(self, value: any, parameter: Parameter, measure: Measure):
        """Set or update parameter with given value.

        Arguments
        ---------
        value
            Value of a parameter to be saved or updated.
        parameter
            Enumerated parameter to be created or updated.
        measure
            Enumerated measure to be found.

        Raises
        -------
        ValueError
            Parameter not found or given unknown measure.

        """
        try:
            index = self._find_param(parameter, measure)
            self._params[index].value = value
        except ValueError:
            param = PluginParam(parameter, measure, value)
            self._params.append(param)
        except Exception as errmsg:
            self._logger.error(errmsg)

    @abstractmethod
    def process_command(self,
                        payload: str,
                        parameter: str,
                        measure: str):
        """Process command for this device."""
        ...

    @abstractmethod
    def process_status(self,
                       device_id: str,
                       payload: str,
                       parameter: str,
                       measure: str):
        """Process status of any device except this one."""
        ...

    @abstractmethod
    def process_data(self,
                     device_id: str,
                     payload: str,
                     parameter: str,
                     measure: str):
        """Process data from any device except this one."""
        ...
