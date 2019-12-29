# -*- coding: utf-8 -*-
"""Module with common functionalities of plugins.

"""
__version__ = '0.1.0'
__status__ = 'Beta'
__author__ = 'Libor Gabaj'
__copyright__ = 'Copyright 2019, ' + __author__
__credits__ = [__author__]
__license__ = 'MIT'
__maintainer__ = __author__
__email__ = 'libor.gabaj@gmail.com'


# Standard library modules
import logging
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Any, NoReturn, List


###############################################################################
# Enumeration and parameter classes
###############################################################################
class Status(Enum):
    """Enumeration of possible status tokens for MQTT topics."""
    ONLINE = 'Online'
    OFFLINE = 'Offline'
    ACTIVE = 'Active'
    IDLE = 'Idle'


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


class Parameter(Enum):
    """Enumeration of expected MQTT topic parameters."""
    ...

class Measure(Enum):
    """Enumeration of possible MQTT topi measures."""
    VALUE = 'val'
    DEFAULT = 'def'
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
    parameter: Parameter = None
    measure: Measure = None
    value: Any = None


class Plugin(ABC):
    """General processing for IoT devices."""

    class Separator(Enum):
        TOPIC = '/'

    def __init__(self) -> NoReturn:
        """Create the class instance - constructor."""
        self.mqtt_client = None
        # Private attributes
        self._params: [PluginData] = []  # Status (configuration) parameters
        self._database: [PluginData] = []  # Data cache
        # Logging
        self._logger = logging.getLogger(' '.join([__name__, __version__]))
        self._logger.debug(
            f'Instance of "{self.__class__.__name__}" created: {self.id}')

    def __str__(self) -> str:
        """Represent instance object as a string."""
        msg = \
            f'{self.__class__.__name__}()'
        return msg

    def __repr__(self) -> str:
        """Represent instance object officially."""
        msg = \
            f'{self.__class__.__name__}()'
        return msg

    @property
    @abstractmethod
    def id(self) -> str:
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
        topic_name = self.Separator.TOPIC.value.join(topic)
        return topic_name

    def get_log(
        self,
        message: str,
        category: Category,
        parameter: str = None,
        measure: Measure = None) -> str:
        """Compose log record as a substitution for MQTT topic and message.

        Arguments
        ---------
        message
            Value originally intended for publishing.
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
        category = category.name
        log = f'{category}'
        if parameter:
            parameter = self.check_parameter(parameter)
            log = f'{log}: {parameter=}'
        if measure:
            measure = self.check_measure(measure)
            log = f'{log}, {measure=}'
        log = f'{log}: {message}'
        return log

    @property
    def device_topic(self) -> str:
        """Compose MQTT topic name for device identifier."""
        topic = [self.id]
        topic.append('#')
        return self.Separator.TOPIC.value.join(topic)

    @abstractmethod
    def begin(self) -> NoReturn:
        """Actions at starting IoT application."""
        self._logger.debug(f'Plugin "{self.id}" started')

    @abstractmethod
    def finish(self) -> NoReturn:
        """Actions at finishing IoT application."""
        self._logger.debug(f'Plugin "{self.id}" stopped')

    def publish_param(self,
                      parameter: Parameter,
                      measure: Optional[Measure]) -> NoReturn:
        """Publish registered parameter to status MQTT topic.

        Arguments
        ---------
        parameter
            Enumerated parameter to be found.
        measure
            Enumerated measure to be found.

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
        msg = self.get_log(
            message,
            Category.STATUS,
            record.parameter,
            record.measure)
        self._logger.debug(msg)
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

    @property
    def database(self) -> List[PluginData]:
        """List of cached data records."""
        return self._database

    def _find_record(self,
                     parameter: Parameter,
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
        ValueError
            Record not found or given unknown measure.

        """
        if parameter is not None:
            self.check_parameter(parameter)
        if measure is not None:
            self.check_measure(measure)
        for index, record in enumerate(dataset):
            if parameter == record.parameter \
                    and (measure is None or measure == record.measure):
                return index
        raise ValueError

    def get_param(self,
                  parameter: Parameter,
                  measure: Optional[Measure]) -> Any:
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

        """
        try:
            index = self._find_record(parameter, measure, self.params)
        except ValueError:
            result = None
        else:
            result = self.params[index].value
        return result

    def set_param(self,
                  value: Any,
                  parameter: Parameter,
                  measure: Optional[Measure]) -> NoReturn:
        """Set or update parameter with given value.

        Arguments
        ---------
        value
            Value of a parameter to be saved or updated.
        parameter
            Enumerated parameter to be created or updated.
        measure
            Enumerated measure to be found.

        """
        try:
            index = self._find_record(parameter, measure, self.params)
            self.params[index].value = value
        except ValueError:
            record = PluginData(parameter, measure, value)
            self.params.append(record)

    def get_value(self,
                  parameter: Parameter,
                  measure: Optional[Measure]) -> Any:
        """Get record value from the device's dataset.

        Arguments
        ---------
        parameter
            Enumerated parameter to be found.
        measure
            Enumerated measure to be found.

        Returns
        -------
            Value of a data record or None.

        """
        try:
            index = self._find_record(parameter, measure, self.database)
        except ValueError:
            result = None
        else:
            result = self.database[index].value
        return result

    def set_value(self,
                  value: Any,
                  parameter: Parameter,
                  measure: Optional[Measure]) -> NoReturn:
        """Set or update record with given value.

        Arguments
        ---------
        value
            Value of a parameter to be saved or updated.
        parameter
            Enumerated parameter to be created or updated.
        measure
            Enumerated measure to be found.

        """
        try:
            index = self._find_record(parameter, measure, self.database)
            self.database[index].value = value
        except ValueError:
            record = PluginData(parameter, measure, value)
            self.database.append(record)

    def process_command(self,
                        value: str,
                        parameter:  Optional[str],
                        measure: Optional[str]) -> NoReturn:
        """Process command for this device."""
        ...

    def process_status(self,
                       value: str,
                       parameter:  Optional[str],
                       measure: Optional[str],
                       device: object) -> NoReturn:
        """Process status of any device except this one."""
        ...

    def process_data(self,
                     value: str,
                     parameter:  Optional[str],
                     measure: Optional[str],
                     device: object) -> NoReturn:
        """Process data from any device except this one."""
        ...
