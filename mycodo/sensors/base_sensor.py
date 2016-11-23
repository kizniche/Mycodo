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

    def stopSensor(self):
        """ temporary.  used by old implementation and the camel case needs to change"""
        logger.warning("Old style `stopSensor()` called by {cls}.  This is depreciated and will be deleted in "
                       "future releases.  Switch to using `stop_sensor` instead.".format(cls=type(self).__name__))
        self.stop_sensor()

    def stop_sensor(self):  # camel case needs to change
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
