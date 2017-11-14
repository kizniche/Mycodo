# coding=utf-8
from __future__ import division

import logging
from .base_input import AbstractInput
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import str_is_float

logger = logging.getLogger("mycodo.inputs.linux_command")


class LinuxCommand(AbstractInput):
    """ A sensor support class that returns a value from a command """

    def __init__(self, command, condition, testing=False):
        super(LinuxCommand, self).__init__()
        self._measurement = None
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
        if self._measurement is None:  # update if needed
            self.read()
        return self._measurement

    def get_measurement(self):
        """ Determine if the return value of the command is a number """
        self._measurement = None

        out, _, _ = cmd_output(self.command)
        if str_is_float(out):
            return float(out)
        else:
            logger.error("The command returned a non-numerical value. "
                         "Ensure only one numerical value is returned "
                         "by the command.")
            return None

    def read(self):
        """
        Executes a command and updates the self._measurement value

        :returns: None on success or 1 on error
        """
        try:
            self._measurement = self.get_measurement()
            if self._measurement is not None:
                return  # success - no errors
        except Exception as e:
            logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
