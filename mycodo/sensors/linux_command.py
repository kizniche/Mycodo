# coding=utf-8
from __future__ import division

import logging
from .base_sensor import AbstractSensor
from utils.system_pi import cmd_output
from utils.system_pi import str_is_float

logger = logging.getLogger("mycodo.sensors.command")


class LinuxCommand(AbstractSensor):
    """ A sensor support class that returns a value from a command """

    def __init__(self, command, condition):
        super(LinuxCommand, self).__init__()
        self._measurement = 0
        self.command = command
        self.condition = str(condition)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(measurement={temp})>".format(
            cls=type(self).__name__,
            temp="{0:.2f}".format(self._measurement))

    def __str__(self):
        """ Return command output """
        return "Measurement: {}".format("{0:.2f}".format(self._measurement))

    def __iter__(self):  # must return an iterator
        """ LinuxCommand iterates through executing a command """
        return self

    def next(self):
        """ Get next measurement """
        if self.read():  # raised an error
            raise StopIteration  # required
        return {self.condition: float('{0:.2f}'.format(self._measurement))}

    @property
    def measurement(self):
        """ Command returns a measurement """
        if not self._measurement:  # update if needed
            self.read()
        return self._measurement

    def get_measurement(self):
        """ Determine if the return value of the command is a number """
        out, _, _ = cmd_output(self.command)
        if str_is_float(out):
            return float(out)
        else:
            return None

    def read(self):
        """
        Executes a command and updates the self._measurement value

        :returns: None on success or 1 on error
        """
        try:
            self._measurement = self.get_measurement()
            return  # success - no errors
        except IOError as e:
            logger.error("{cls}.get_measurement() method raised IOError: "
                         "{err}".format(cls=type(self).__name__, err=e))
        except Exception as e:
            logger.exception("{cls} raised an exception when taking a reading: "
                             "{err}".format(cls=type(self).__name__, err=e))
        return 1
