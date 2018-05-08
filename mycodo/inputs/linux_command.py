# coding=utf-8
import logging

from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import str_is_float
from .base_input import AbstractInput


class LinuxCommand(AbstractInput):
    """ A sensor support class that returns a value from a command """

    def __init__(self, input_dev, testing=False):
        super(LinuxCommand, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.linux_command")
        self._measurement = None
        self.cmd_measurement = 'measurement'

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.linux_command_{id}".format(id=input_dev.id))
            self.cmd_command = input_dev.cmd_command
            self.cmd_measurement = str(input_dev.cmd_measurement)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(measurement={cond})>".format(
            cls=type(self).__name__,
            cond="{0:.2f}".format(self._measurement))

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
        return {self.cmd_measurement: float('{0:.2f}'.format(self._measurement))}

    @property
    def measurement(self):
        """ Command returns a measurement """
        if self._measurement is None:  # update if needed
            self.read()
        return self._measurement

    def get_measurement(self):
        """ Determine if the return value of the command is a number """
        self._measurement = None

        out, _, _ = cmd_output(self.cmd_command)
        if str_is_float(out):
            return float(out)
        else:
            self.logger.error("The command returned a non-numerical value. "
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
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
