# coding=utf-8
from __future__ import division

import logging
import subprocess
from .base_sensor import AbstractSensor

logger = logging.getLogger(__name__)


class RaspberryPiCPUTemp(AbstractSensor):
    """ A sensor support class that monitors the raspberry pi's cpu temperature """

    def __init__(self):
        super(RaspberryPiCPUTemp, self).__init__()
        self._temperature = 0

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})>".format(
            cls=type(self).__name__,
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return temperature information """
        return "temperature: {}".format("{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ RaspberryPiCPUTemp iterates through live temperature readings """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature=float('{0:.2f}'.format(self._temperature)))

    @staticmethod
    def get_measurement():
        """ Gets the Raspberry pi's temperature in Celsius by reading the temp file and div by 1000 """
        with open('/sys/class/thermal/thermal_zone0/temp') as cpu_temp_file:
            return float(cpu_temp_file.read()) / 1000

    @property
    def temperature(self):
        """ CPU temperature in celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def read(self):
        """
        Takes a reading from the CPU and updates the self._temperature value

        :returns: None on success or 1 on error
        """
        try:
            self._temperature = self.get_measurement()
            return  # success - no errors
        except IOError as e:
            logger.error("CPU temperature reading returned IOError: "
                         "{err}".format(err=e))
        except Exception as e:
            logger.error("{cls} raised an exception when taking a reading: "
                         "{err}".format(cls=type(self).__name__, err=e))
        return 1


class RaspberryPiGPUTemp(AbstractSensor):
    """ A sensor support class that monitors the raspberry pi's gpu temperature """

    def __init__(self):
        super(RaspberryPiGPUTemp, self).__init__()
        self._temperature = 0

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})>".format(
            cls=type(self).__name__,
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return temperature information """
        return "temperature: {}".format("{0:.2f}".format(self._temperature))

    def __iter__(self):
        """ Support the iterator protocol """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature=float('{0:.2f}'.format(self._temperature)))

    def read(self):
        """ updates the self._temperature """
        try:
            self._temperature = self.get_measurement()
            return  # success - no errors
        except subprocess.CalledProcessError as e:
            logger.error("{cls}.get_measurement() subprocess call raised: "
                         "{err}".format(cls=type(self).__name__, err=e))
        except IOError as e:
            logger.error("{cls}.get_measurement() method raised IOError: "
                         "{err}".format(cls=type(self).__name__, err=e))
        except Exception as e:
            logger.error("{cls} raised an exception when taking a reading: "
                         "{err}".format(cls=type(self).__name__, err=e))

        # After any error return 1
        return 1

    @staticmethod
    def get_measurement():
        """ Calls the vcgencmd in a subprocess and reads the GPU temperature """
        gputempstr = subprocess.check_output(('/opt/vc/bin/vcgencmd', 'measure_temp'))  # example output: temp=42.8'C
        return float(gputempstr.split('=')[1].split("'")[0])

    @property
    def temperature(self):
        """ returns the last temperature """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature
