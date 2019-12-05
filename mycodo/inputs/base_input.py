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
import time

import filelock
import os

from mycodo.databases.models import Conversion
from mycodo.databases.models import DeviceMeasurements
from mycodo.utils.database import db_retrieve_table_daemon


class AbstractInput(object):
    """
    Base Input class that ensures certain methods and values are present
    in inputs.
    """
    def __init__(self, input_dev, testing=False, name=__name__):

        self.logger = None
        self.setup_logger(testing=testing, name=name, input_dev=input_dev)
        self.input_dev = input_dev
        self._measurements = None
        self.channels_conversion = {}
        self.channels_measurement = {}
        self.lock = {}
        self.lock_file = None
        self.locked = {}
        self.return_dict = {}
        self.avg_max = {}
        self.avg_index = {}
        self.avg_meas = {}
        self.acquiring_measurement = False
        self.running = True
        self.device_measurements = None

        if not testing:
            self.unique_id = input_dev.unique_id
            self.initialize_measurements()

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
        finally:
            # Clean up
            if self.lock_file in self.locked and self.locked[self.lock_file]:
                self.lock_release(self.lock_file)
        return 1

    def initialize_measurements(self):
        try:
            if self.device_measurements:
                return
        except:
            pass
        self.setup_device_measurement()

    def is_enabled(self, channel):
        try:
            return self.channels_measurement[channel].is_enabled
        except:
            self.setup_device_measurement()
            return self.channels_measurement[channel].is_enabled

    def setup_custom_options(self, custom_options, input_dev):
        for each_option_default in custom_options:
            try:
                required = False
                custom_option_set = False
                error = []
                if 'type' not in each_option_default:
                    error.append("'type' not found in custom_options")
                if 'id' not in each_option_default:
                    error.append("'id' not found in custom_options")
                if 'default_value' not in each_option_default:
                    error.append(
                        "'default_value' not found in custom_options")
                for each_error in error:
                    self.logger.error(each_error)
                if error:
                    return

                if ('required' in each_option_default and
                        each_option_default['required']):
                    required = True

                option_value = each_option_default['default_value']

                if not hasattr(input_dev, 'custom_options'):
                    self.logger.error("input_dev missing attribute custom_options")
                    return

                if input_dev.custom_options:
                    for each_option in input_dev.custom_options.split(';'):
                        option = each_option.split(',')[0]
                        value = each_option.split(',')[1]

                        if option == each_option_default['id']:
                            custom_option_set = True
                            option_value = value

                if required and not custom_option_set:
                    self.logger.error(
                        "Custom option '{}' required but was not found to be "
                        "set by the user".format(each_option_default['id']))

                if each_option_default['type'] == 'integer':
                    setattr(
                        self, each_option_default['id'], int(option_value))
                elif each_option_default['type'] == 'float':
                    setattr(
                        self, each_option_default['id'], float(option_value))
                elif each_option_default['type'] == 'bool':
                    setattr(
                        self, each_option_default['id'], bool(option_value))
                elif each_option_default['type'] == 'text':
                    setattr(
                        self, each_option_default['id'], str(option_value))
                elif each_option_default['type'] == 'select':
                    setattr(
                        self, each_option_default['id'], str(option_value))
                else:
                    self.logger.error(
                        "Unknown custom_option type '{}'".format(
                            each_option_default['type']))
            except Exception:
                self.logger.exception("Error parsing custom_options")

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
            time.sleep(1)

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
        """ Not used yet """
        self.running = True

    def stop_input(self):
        """ Called when Input is deactivated """
        self.running = False
        try:
            if self.lock_file:
                self.lock_release(self.lock_file)
        except:
            pass

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

    def lock_acquire(self, lockfile, timeout):
        """ Non-blocking locking method """
        self.lock[lockfile] = filelock.FileLock(lockfile, timeout=1)
        self.locked[lockfile] = False
        timer = time.time() + timeout
        self.logger.debug("Acquiring lock for {} ({} sec timeout)".format(
            lockfile, timeout))
        while self.running and time.time() < timer:
            try:
                self.lock[lockfile].acquire()
                seconds = time.time() - (timer - timeout)
                self.logger.debug(
                    "Lock acquired for {} in {:.3f} seconds".format(
                        lockfile, seconds))
                self.locked[lockfile] = True
                break
            except:
                pass
            time.sleep(0.05)
        if not self.locked[lockfile]:
            self.logger.debug(
                "Lock unable to be acquired after {:.3f} seconds. "
                "Breaking for future lock.".format(timeout))
            self.lock_release(self.lock_file)

    def lock_release(self, lockfile):
        """ Release lock and force deletion of lock file """
        try:
            self.logger.debug("Releasing lock for {}".format(lockfile))
            self.lock[lockfile].release(force=True)
            os.remove(lockfile)
        except Exception:
            pass
        finally:
            self.locked[lockfile] = False

    def is_acquiring_measurement(self):
        return self.acquiring_measurement
