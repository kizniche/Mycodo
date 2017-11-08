# coding=utf-8
"""
This module contains the AbstractSensor Class which acts as a template
for all sensors.  It is not to be used directly.  The AbstractSensor Class
ensures that certain methods and instance variables are included in each
Sensor.

All Sensors should inherit from this class and overwrite methods that raise
NotImplementedErrors
"""
import logging

logger = logging.getLogger('mycodo.sensors.base_sensor')


class AbstractSensor(object):
    """
    Base sensor class that ensures certain methods and values are present
    in sensors.

    This class is not to be used directly.  It is to be inherited by sensor classes.

     example:
         class MyNewSensor(AbstractSensor):
             ... do stuff

    """

    def __init__(self):
        self.avg_max = {}
        self.avg_index = {}
        self.avg_meas = {}
        self.running = True

    def __iter__(self):
        """ Support the iterator protocol """
        return self

    def __next__(self):
        return self.next()

    def next(self):
        """
        Get next temperature reading.  Required by iterators.  Must raise StopIterator
        when exhausted.

        This method calls read() to update the sensor data and then
        returns a dict containing the measurement type as the key and the value

        example:
            def next(self):
                ''' example of next method '''
                if self.read():  # take measurement raised an error
                    raise StopIteration  # required behavior
                return dict(temperature=float('{0:.2f}'.format(self._temperature)))

        :returns dict: dict(measurement_type=value)
        :rtype: dict
        """
        logger.error("{cls} did not overwrite the next() method.  All subclasses of the AbstractSensor class"
                     " are required to overwrite this method".format(cls=type(self).__name__))
        raise NotImplementedError

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
                logger.error("init_max must be greater than 1")
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

    def stop_sensor(self):
        """ Called by SensorController class when sensors are deactivated """
        self.running = False

    def start_sensor(self):
        """ Not used yet """
        self.running = True

    def read(self):
        """ Causes the sensor to take a reading """
        logger.error("{cls} did not overwrite the read() method.  All subclasses of the AbstractSensor class"
                     " are required to overwrite this method".format(cls=type(self).__name__))
        raise NotImplementedError
