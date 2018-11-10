# coding=utf-8
"""
This module contains the AbstractInput Class which acts as a template
for all inputs.  It is not to be used directly.  The AbstractInput Class
ensures that certain methods and instance variables are included in each
Input.

All Inputs should inherit from this class and overwrite methods that raise
NotImplementedErrors
"""
import logging

from sqlalchemy import and_

from mycodo.databases.models import InputMeasurements


class AbstractInput(object):
    """
    Base sensor class that ensures certain methods and values are present
    in inputs.

    This class is not to be used directly.  It is to be inherited by sensor classes.

     example:
         class MyNewSensor(AbstractInput):
             ... do stuff

    """

    def __init__(self, run_main=False):
        self.logger = logging.getLogger('mycodo.inputs.base_input')
        self.run_main = run_main
        self._measurements = None
        self.avg_max = {}
        self.avg_index = {}
        self.avg_meas = {}
        self.acquiring_measurement = False
        self.running = True
        self.input_measurements = None

    def __iter__(self):
        """ Support the iterator protocol """
        return self

    def __repr__(self):
        """  Representation of object """
        return_str = '<{cls}'.format(cls=type(self).__name__)
        if self._measurements:
            for each_measurement, unit_data in self._measurements.items():
                for each_unit, channel_data in unit_data.items():
                    for each_channel in channel_data:
                        return_str = '{prev}({meas},{unit},{chan},{val})'.format(
                            prev=return_str,
                            meas=each_measurement,
                            unit=each_unit,
                            chan=each_channel,
                            val=self._measurements[each_measurement][each_unit][each_channel])
            return_str = '{prev}>'.format(prev=return_str)
            return return_str
        else:
            return "Measurements dictionary empty"

    def __str__(self):
        """ Return measurement information """
        return_str = ''
        skip_first_separator = False
        if self._measurements:
            for each_measurement, unit_data in self._measurements.items():
                for each_unit, channel_data in unit_data.items():
                    for each_channel in channel_data:
                        if skip_first_separator:
                            return_str = '{prev};'.format(prev=return_str)
                        else:
                            skip_first_separator = True
                        return_str = '{prev}{meas},{unit},{chan},{val}'.format(
                            prev=return_str,
                            meas=each_measurement,
                            unit=each_unit,
                            chan=each_channel,
                            val=self._measurements[each_measurement][each_unit][each_channel])
            return return_str
        else:
            return "Measurements dictionary empty"

    def __next__(self):
        return self.next()

    def next(self):
        """ Get next measurement reading """
        self._measurements = None
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
        try:
            self._measurements = self.get_measurement()
            if self._measurements is not None:
                return  # success - no errors
        except IOError as e:
            self.logger.error(
                "{cls}.get_measurement() method raised IOError: "
                "{err}".format(cls=type(self).__name__, err=e))
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1

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

    def is_enabled(self, channel):
        if self.run_main:
            return True
        elif (self.input_measurements and
                self.input_measurements.filter(and_(
                    InputMeasurements.is_enabled == True,
                    InputMeasurements.channel == channel)).count()):
            return True

    def stop_sensor(self):
        """ Called when sensors are deactivated """
        self.running = False

    def start_sensor(self):
        """ Not used yet """
        self.running = True

    def is_acquiring_measurement(self):
        return self.acquiring_measurement
