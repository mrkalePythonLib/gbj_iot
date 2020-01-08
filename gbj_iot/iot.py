# -*- coding: utf-8 -*-
"""Module with common functionalities of plugins.

"""
__version__ = '0.1.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2019-2020, ' + __author__
__credits__ = [__author__]
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'


# Standard library modules
import logging
from os import path
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any, NoReturn, List


###############################################################################
# Enumerations utilized by all plugins
###############################################################################
class Status(Enum):
    """Enumeration of possible status tokens for MQTT topics."""
    ONLINE = 'Online'
    OFFLINE = 'Offline'
    ACTIVE = 'Active'
    IDLE = 'Idle'
    UNKNOWN = 'Uknown'


class Command(Enum):
    """Enumeration of possible commands tokens for MQTT topics."""
    GET_STATUS = 'STATUS'
    RESET = 'RESET'
    TURN_ON = 'ON'
    TURN_OFF = 'OFF'
    TOGGLE = 'TOGGLE'


class Category(Enum):
    """Enumeration of possible MQTT topic parameters."""
    STATUS = 'state'
    COMMAND = 'cmd'
    DATA = 'data'


class Measure(Enum):
    """Enumeration of possible MQTT topi measures."""
    VALUE = 'val'
    DEFAULT = 'dft'
    MINIMUM = 'min'
    MAXIMUM = 'max'
    AVERAGE = 'avg'
    PERCENTILE = 'ptl'
    PERCENTAGE = 'perc'


###############################################################################
# IoT core
###############################################################################
@dataclass
class PluginData:
    """Plugin parameter record definition."""
    parameter: Enum = None
    measure: Measure = None
    value: Any = None


class Plugin(ABC):
    """General processing for IoT devices."""

    class Separator(Enum):
        """Enumeration of separators in structural strings."""
        TOPIC = '/'

    def __init__(self) -> NoReturn:
        """Create the class instance - constructor."""
        # Private attributes
        self._params: [PluginData] = []  # Status (configuration) parameters
        # Device handlers
        self.config = None  # Access to configuration INI file
        self.mqtt_client = None  # Access to MQTT broker
        self.userdata = None  # Injected user data from received messages
        # Logging
        log = f'Instance of "{self.__class__.__name__}" created: {self.did}'
        self._logger = logging.getLogger(' '.join([__name__, __version__]))
        self._logger.debug(log)

    def __str__(self) -> str:
        """Represent instance object as a string."""
        return f'{self.__class__.__name__}()'

    def __repr__(self) -> str:
        """Represent instance object officially."""
        return f'{self.__class__.__name__}()'

    @property
    @abstractmethod
    def did(self) -> str:
        """Identifier of the plugin and the root MQTT topic fragment."""
        ...

    def get_did(self, name: str) -> str:
        """Compose plugin identifier from provided module name."""
        name = path.splitext(name)[0]
        device_id = name.split('_')[1]
        return device_id

    def get_topic(
            self,
            category: Category,
            parameter: Enum = None,
            measure: Measure = None) -> str:
        """Compose MQTT topic name from prescribed topic parts.

        Arguments
        ---------
        category
            Enumerated category of an MQTT topic.
        parameter
            Optional enumerated parameter, which value is transmitted
            by an MQTT topic. It is usually a name of a physical unit
            or an operational parameter.
        measure
            Optional enumerated measure of an aspect related to tranmitted
            value. It is usually a statistical measure like minimum, maximum,
            current value, etc.

        """
        topic = [self.did]
        topic.append(category.value)
        # Optional topic parts
        if parameter:
            topic.append(parameter.value)
        if measure:
            topic.append(measure.value)
        # Compose topic
        topic_name = self.Separator.TOPIC.value.join(topic)
        return topic_name

    def get_log(
            self,
            message: str,
            category: Category,
            parameter: Enum = None,
            measure: Measure = None) -> str:
        """Compose log record as a substitution for MQTT topic and message.

        Arguments
        ---------
        message
            Value originally intended for publishing.
        category
            Enumerated category of a MQTT topic.
        parameter
            Optional enumerated parameter, which value is transmitted
            by an MQTT topic. It is usually a name of a physical unit
            or an operational parameter.
        measure
            Optional enumerated measure of an aspect related to tranmitted
            value. It is usually a statistical measure like minimum, maximum,
            current value, etc.

        """
        category = category.name
        log = f'{category}'
        if parameter:
            parameter = parameter.value
            log = f'{log}: {parameter=}'
        if measure:
            measure = measure.value
            log = f'{log}, {measure=}'
        log = f'{log}: {message}'
        return log

    @property
    def device_topic(self) -> str:
        """Compose MQTT topic name for device identifier."""
        topic = [self.did]
        topic.append('#')
        return self.Separator.TOPIC.value.join(topic)

    @abstractmethod
    def begin(self) -> NoReturn:
        """Actions at starting IoT application."""
        log = f'Plugin "{self.did}" started'
        self._logger.debug(log)

    def finish(self) -> NoReturn:
        """Actions at finishing IoT application."""
        log = f'Plugin "{self.did}" stopped'
        self._logger.debug(log)

    def publish_param(self,
                      parameter: Enum = None,
                      measure: Measure = None) -> NoReturn:
        """Publish registered parameter to status MQTT topic.

        Arguments
        ---------
        parameter
            Optional enumerated parameter to be found.
        measure
            Optional enumerated measure to be found.

        """
        try:
            index = self._find_record(parameter, measure, self.params)
        except ValueError:
            return
        record = self.params[index]
        message = f'{record.value}'
        topic = self.get_topic(
            Category.STATUS,
            record.parameter,
            record.measure)
        log = self.get_log(
            message,
            Category.STATUS,
            record.parameter,
            record.measure)
        self._logger.debug(log)
        self.mqtt_client.publish(message, topic)

    def publish_status(self) -> NoReturn:
        """Publish all registered parameters to status MQTT topic."""
        for record in self.params:
            self.publish_param(record.parameter, record.measure)


###############################################################################
# Parameters and data actions
###############################################################################
    @property
    def params(self) -> List[PluginData]:
        """List of registered parameters."""
        return self._params

    def _find_record(self,
                     parameter: Optional[Enum],
                     measure: Optional[Measure],
                     dataset: List[PluginData]) -> int:
        """Find record in the device's dataset.

        Arguments
        ---------
        parameter
            Enumerated parameter to be found.
        measure
            Enumerated measure to be found.
        dataset
            List of data records for searching in.

        Returns
        -------
            Index of found record in the list of a dataset.

        Raises
        -------
        AttributeError
            Argument parameter and/or measure is not an enumeration, so that
            they have no attribure value.
        ValueError
            No record found.

        """
        for index, record in enumerate(dataset):
            if parameter.value == record.parameter \
                    and (measure.value is None \
                         or measure.value == record.measure):
                return index
        raise ValueError

    def get_param(self,
                  parameter: Enum = None,
                  measure: Measure = None,
                  default: Any = None) -> Any:
        """Get parameter value from the device's parameters list.

        Arguments
        ---------
        parameter
            Optional enumerated parameter to be found.
        measure
            Optional enumerated measure to be found.
        default
            Default value in case that nothing is found in the dataset.

        Returns
        -------
            Value of a parameter or default value.

        """
        try:
            index = self._find_record(parameter, measure, self.params)
        except ValueError:
            result = default
        else:
            result = self.params[index].value
        return result

    def set_param(self,
                  value: Any,
                  parameter: Enum = None,
                  measure: Measure = None) -> NoReturn:
        """Set or update parameter with given value.

        Arguments
        ---------
        value
            Value of a parameter to be saved or updated.
        parameter
            Optional enumerated parameter to be created or updated.
        measure
            Optional enumerated measure to be found.

        """
        try:
            index = self._find_record(parameter, measure, self.params)
            self.params[index].value = value
        except ValueError:
            record = PluginData(parameter, measure, value)
            self.params.append(record)

    def process_own_command(self,
                            value: str,
                            parameter: Optional[str],
                            measure: Optional[str]) -> NoReturn:
        """Process command for this device only.

        Arguments
        ---------
        value
            Payload from an MQTT message.
        parameter
            Parameter taken from an MQTT topic corresponding to some item value
            from Parameter enumeration.
        measure
            Measure taken from an MQTT topic corresponding to some item value
            from Measure enumeration.

        """
        ...

    def process_command(self,
                       value: str,
                       parameter: Optional[str],
                       measure: Optional[str],
                       device: 'Plugin') -> NoReturn:
        """Process command for any device except this one.

        Arguments
        ---------
        value
            Payload from an MQTT message.
        parameter
            Parameter taken from an MQTT topic corresponding to some item value
            from Parameter enumeration.
        measure
            Measure taken from an MQTT topic corresponding to some item value
            from Measure enumeration.
        device
            Object of a sourcing device (plugin), which sent an MQTT message.

        """
        ...

    def process_status(self,
                       value: str,
                       parameter: Optional[str],
                       measure: Optional[str],
                       device: 'Plugin') -> NoReturn:
        """Process status of any device except this one.

        Arguments
        ---------
        value
            Payload from an MQTT message.
        parameter
            Parameter taken from an MQTT topic corresponding to some item value
            from Parameter enumeration.
        measure
            Measure taken from an MQTT topic corresponding to some item value
            from Measure enumeration.
        device
            Object of a sourcing device (plugin), which sent an MQTT message.

        """
        ...

    def process_data(self,
                     value: str,
                     parameter: Optional[str],
                     measure: Optional[str],
                     device: 'Plugin') -> NoReturn:
        """Process data from any device except this one.

        Arguments
        ---------
        value
            Payload from an MQTT message.
        parameter
            Parameter taken from an MQTT topic corresponding to some item value
            from Parameter enumeration.
        measure
            Measure taken from an MQTT topic corresponding to some item value
            from Measure enumeration.
        device
            Object of a sourcing device (plugin), which sent an MQTT message.

        """
        ...
