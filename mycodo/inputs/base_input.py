# coding=utf-8
"""
This module contains the AbstractInput Class which acts as a template
for all inputs.  It is not to be used directly.  The AbstractInput Class
ensures that certain methods and instance variables are included in each
Input.

All Inputs should inherit from this class and overwrite methods that raise
NotImplementedErrors
"""
import datetime
import logging
import time

import filelock
import os

from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.database import db_retrieve_table_daemon


class AbstractInput(object):
    """
    Base sensor class that ensures certain methods and values are present
    in inputs.

    This class is not to be used directly.  It is to be inherited by sensor classes.

     example:
         class MyNewSensor(AbstractInput):
             ... do stuff

    """

    def __init__(self, input_dev, testing=False, name=__name__):
        self.logger = None
        self.setup_logger(testing=testing, name=name, input_dev=input_dev)
        self.input_dev = input_dev
        self._measurements = None
        self.channels_conversion = {}
        self.channels_measurement = {}
        self.lock = None
        self.lock_file = None
        self.locked = False
        self.return_dict = {}
        self.avg_max = {}
        self.avg_index = {}
        self.avg_meas = {}
        self.acquiring_measurement = False
        self.running = True
        self.device_measurements = None

        if not testing:
            self.unique_id = input_dev.unique_id
            self.check_setup()

    def __iter__(self):
        """ Support the iterator protocol """
        return self

    def __repr__(self):
        """  Representation of object """
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
        """ Return measurement information """
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
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return self.measurements

    @property
    def measurements(self):
        """ Store measurements """
        if self._measurements is None:  # update if needed
            self.read()
        return self._measurements

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
        self.check_setup()
        try:
            self._measurements = self.get_measurement()
            if self._measurements is not None:
                return  # success - no errors
        except TimeoutError as error:
            self.logger.error("Error: {}".format(error))
        except IOError as e:
            self.logger.error(
                "{cls}.get_measurement() method raised IOError: "
                "{err}".format(cls=type(self).__name__, err=e))
        except Exception as e:
            msg = "{cls} raised an exception when taking a reading: " \
                  "{err}".format(cls=type(self).__name__, err=e)
            if logging.getLevelName(self.logger.getEffectiveLevel()) == 'DEBUG':
                self.logger.exception(msg)
            else:
                self.logger.error(msg)

        # Clean up
        self.lock_release()

        return 1

    def lock_acquire(self, lockfile, timeout):
        self.lock = filelock.FileLock(lockfile, timeout=1)
        self.locked = False
        timer = time.time() + timeout
        self.logger.debug("Acquiring lock for {} ({} sec timeout)".format(
            lockfile, timeout))
        while self.running and time.time() < timer:
            try:
                self.lock.acquire()
                seconds = time.time() - (timer - timeout)
                self.logger.debug(
                    "Lock acquired for {} in {:.2f} seconds".format(
                        lockfile, seconds))
                self.locked = True
                break
            except:
                pass
        if not self.locked:
            self.logger.debug(
                "Lock unable to be acquired after {:.2f} seconds. "
                "Breaking for future lock.".format(timeout))
            self.lock_release()

    def lock_release(self):
        try:
            self.lock.release(force=True)
        except:
            pass

    def get_value(self, channel):
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

    def set_value(self, channel, value, timestamp=None):
        """
        Sets the measurement value for a channel
        :param channel: measurement channel
        :type channel: int
        :param value: measurement value
        :type value: float
        :param timestamp: measurement timestamp
        :type timestamp: datetime.datetime
        :return:
        """
        self.return_dict[channel]['value'] = value
        self.return_dict[channel]['timestamp_utc'] = timestamp if timestamp else datetime.datetime.utcnow()

    def filter_average(self, name, init_max=0, measurement=None):
        """
        Return the average of several recent measurements
        Use to smooth erratic measurements

        :param name: name of the measurement
        :param init_max: initialize variables for this name
        :param measurement: add measurement to pool and return average of past init_max measurements
        :return: int or float, whichever measurements come in as
        """
        if name not in self.avg_max:
            if init_max != 0 and init_max < 2:
                self.logger.error("init_max must be greater than 1")
            elif init_max > 1:
                self.avg_max[name] = init_max
                self.avg_meas[name] = []
                self.avg_index[name] = 0

        if measurement is None:
            return

        if 0 <= self.avg_index[name] < len(self.avg_meas[name]):
            self.avg_meas[name][self.avg_index[name]] = measurement
        else:
            self.avg_meas[name].append(measurement)
        average = sum(self.avg_meas[name]) / float(len(self.avg_meas[name]))

        if self.avg_index[name] >= self.avg_max[name] - 1:
            self.avg_index[name] = 0
        else:
            self.avg_index[name] += 1

        return average

    def check_setup(self):
        try:
            if not self.device_measurements:
                self.setup_device_measurement()
        except:
            self.setup_device_measurement()

    def setup_device_measurement(self):
        # Make 5 attempts to access database
        for _ in range(5):
            try:
                self.device_measurements = db_retrieve_table_daemon(
                    DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == self.input_dev.unique_id)

                for each_measure in self.device_measurements.all():
                    self.channels_measurement[each_measure.channel] = each_measure
                    self.channels_conversion[each_measure.channel] = db_retrieve_table_daemon(
                        Conversion, unique_id=each_measure.conversion_id)
                return
            except Exception as msg:
                self.logger.debug("Error: {}".format(msg))
            time.sleep(3)

    def is_enabled(self, channel):
        try:
            return self.channels_measurement[channel].is_enabled
        except:
            self.setup_device_measurement()
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

    def stop_sensor(self):
        """ Called when sensors are deactivated """
        self.running = False

    def start_sensor(self):
        """ Not used yet """
        self.running = True

    @staticmethod
    def str_is_float(str_value):
        try:
            test = float(str(str_value))
            return True
        except:
            return False

    def is_acquiring_measurement(self):
        return self.acquiring_measurement
