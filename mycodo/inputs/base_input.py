# coding=utf-8
"""
This module contains the AbstractInput Class which acts as a template
for all inputs.  It is not to be used directly. The AbstractInput Class
ensures that certain methods and instance variables are included in each
Input.

All Inputs should inherit from this class and overwrite methods that raise
NotImplementedErrors
"""
import datetime
import logging

from mycodo.abstract_base_controller import AbstractBaseController
from mycodo.databases.models import Input


class AbstractInput(AbstractBaseController):
    """
    Base Input class that ensures certain methods and values are present
    in inputs.
    """
    def __init__(self, input_dev, testing=False, name=__name__):
        if not testing:
            super().__init__(input_dev.unique_id, testing=testing, name=__name__)
        else:
            super().__init__(None, testing=testing, name=__name__)

        self.logger = None
        self.setup_logger(testing=testing, name=name, input_dev=input_dev)
        self.input_dev = input_dev
        self._measurements = None
        self.return_dict = {}
        self.filter_avg = {}
        self.avg_max = {}
        self.avg_index = {}
        self.avg_meas = {}
        self.acquiring_measurement = False
        self.running = True

        if not testing:
            self.unique_id = input_dev.unique_id
            self.initialize_measurements()

    def __iter__(self):
        """Support the iterator protocol."""
        return self

    def __repr__(self):
        """Representation of object."""
        return_str = '<{cls}'.format(cls=type(self).__name__)
        if self._measurements:
            for each_channel, channel_data in self._measurements.items():
                return_str += '({ts},{chan},{meas},{unit},{val})'.format(
                    ts=channel_data['time'],
                    chan=each_channel,
                    meas=channel_data['measurement'],
                    unit=channel_data['unit'],
                    val=channel_data['value'])
            return_str += '>'
            return return_str
        else:
            return "Measurements dictionary empty"

    def __str__(self):
        """Return measurement information."""
        return_str = ''
        skip_first_separator = False
        if self._measurements:
            for each_channel, channel_data in self._measurements.items():
                if skip_first_separator:
                    return_str += ';'
                else:
                    skip_first_separator = True
                return_str += '{ts},{chan},{meas},{unit},{val}'.format(
                    ts=channel_data['time'],
                    chan=each_channel,
                    meas=channel_data['measurement'],
                    unit=channel_data['unit'],
                    val=channel_data['value'])
            return return_str
        else:
            return "Measurements dictionary empty"

    def __next__(self):
        return self.next()

    def next(self):
        """Get next measurement reading."""
        if self.read():  # raised an error
            raise StopIteration  # required
        return self.measurements

    @property
    def measurements(self):
        """Store measurements."""
        if self._measurements is None:  # update if needed
            self.read()
        return self._measurements

    def initialize(self):
        self.logger.error(
            "{cls} did not overwrite the initialize() method. All "
            "subclasses of the AbstractInput class are required to overwrite "
            "this method".format(cls=type(self).__name__))
        raise NotImplementedError

    def get_measurement(self):
        self.logger.error(
            "{cls} did not overwrite the get_measurement() method. All "
            "subclasses of the AbstractInput class are required to overwrite "
            "this method".format(cls=type(self).__name__))
        raise NotImplementedError

    def read(self):
        """
        Takes a reading

        :returns: None on success or 1 on error
        """
        self._measurements = None
        try:
            self._measurements = self.get_measurement()
            if self._measurements is not None:
                return  # success - no errors
        except TimeoutError as error:
            msg = "TimeoutError: {}".format(error)
            if logging.getLevelName(self.logger.getEffectiveLevel()) == 'DEBUG':
                self.logger.exception(msg)
            else:
                self.logger.error(msg)
        except IOError as e:
            msg = "{cls}.get_measurement() method raised IOError: " \
                  "{err}".format(cls=type(self).__name__, err=e)
            if logging.getLevelName(self.logger.getEffectiveLevel()) == 'DEBUG':
                self.logger.exception(msg)
            else:
                self.logger.error(msg)
        except Exception as e:
            msg = "{cls} raised an exception when taking a reading: " \
                  "{err}".format(cls=type(self).__name__, err=e)
            if logging.getLevelName(self.logger.getEffectiveLevel()) == 'DEBUG':
                self.logger.exception(msg)
            else:
                self.logger.error(msg)
        return 1

    def initialize_measurements(self):
        try:
            if self.device_measurements:
                return
        except:
            pass
        self.setup_device_measurement(self.unique_id)

    def is_enabled(self, channel):
        if channel not in self.channels_measurement:
            self.logger.error(f"Channel {channel} not found by is_enabled()")
            return
        try:
            return self.channels_measurement[channel].is_enabled
        except:
            self.setup_device_measurement(self.unique_id)
            return self.channels_measurement[channel].is_enabled

    def setup_logger(self, testing=None, name=None, input_dev=None):
        name = name if name else __name__
        if not testing and input_dev:
            log_name = "{}_{}".format(name, input_dev.unique_id.split('-')[0])
        else:
            log_name = name
        self.logger = logging.getLogger(log_name)
        if not testing and input_dev:
            if input_dev.log_level_debug:
                self.logger.setLevel(logging.DEBUG)
            else:
                self.logger.setLevel(logging.INFO)
            
    def start_input(self):
        """Not used yet."""
        self.running = True
    
    def pre_stop(self):
        """Executed when the controller is instructed to stop."""
        pass

    def stop_input(self):
        """Called when Input is deactivated."""
        self.running = False

    def value_get(self, channel):
        """
        Returns the value of a channel, if set.
        :param channel: measurement channel
        :type channel: int
        :return: measurement value
        :rtype: float
        """
        if (channel in self.return_dict and
                'value' in self.return_dict[channel]):
            return self.return_dict[channel]['value']

    def value_set(self, chan, value, timestamp=None):
        """
        Sets the measurement value for a channel
        :param chan: measurement channel
        :type chan: int
        :param value: measurement value
        :type value: float
        :param timestamp: measurement timestamp
        :type timestamp: datetime.datetime
        :return:
        """
        if value is None:
            self.logger.error(
                f"Error 100: Cannot set a value of '{value}' of type {type(value)}. Must be a float or string "
                f"representing a float. See https://kizniche.github.io/Mycodo/Error-Codes#error-100 for more info.")
            return

        if not self.is_enabled(chan):
            return

        self.return_dict[chan]['value'] = float(value)

        if timestamp:
            self.return_dict[chan]['timestamp_utc'] = timestamp
        else:
            self.return_dict[chan]['timestamp_utc'] = datetime.datetime.utcnow()

    #
    # Accessory functions
    #

    def filter_average(self, name, init_max=0, measurement=None):
        """
        Return the average of several recent measurements
        Use to smooth erratic measurements

        :param name: name of the measurement
        :param init_max: initialize_measurements variables for this name
        :param measurement: add measurement to pool and return average of past init_max measurements
        :return: int or float, whichever measurements come in as
        """
        if name not in self.filter_avg:
            self.filter_avg[name] = {}
            if init_max < 2:
                self.logger.error("init_max must be greater than 1")
            else:
                self.filter_avg[name]['max'] = init_max
                self.filter_avg[name]['meas'] = []
                self.filter_avg[name]['index'] = 0

        if measurement is None:
            return

        if 0 <= self.filter_avg[name]['index'] < len(self.filter_avg[name]['meas']):
            self.filter_avg[name]['meas'][self.filter_avg[name]['index']] = measurement
        else:
            self.filter_avg[name]['meas'].append(measurement)
        average = sum(self.filter_avg[name]['meas']) / float(len(self.filter_avg[name]['meas']))

        if self.filter_avg[name]['index'] >= self.filter_avg[name]['max'] - 1:
            self.filter_avg[name]['index'] = 0
        else:
            self.filter_avg[name]['index'] += 1

        return average

    def is_acquiring_measurement(self):
        return self.acquiring_measurement

    def set_custom_option(self, option, value):
        return self._set_custom_option(Input, self.unique_id, option, value)

    def get_custom_option(self, option, default_return=None):
        return self._get_custom_option(Input, self.unique_id, option, default_return=default_return)

    def delete_custom_option(self, option):
        return self._delete_custom_option(Input, self.unique_id, option)
