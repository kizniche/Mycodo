# coding=utf-8
import logging

from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import str_is_float
from mycodo.inputs.base_input import AbstractInput

# Input information
INPUT_INFORMATION = {
    'unique_name_input': 'LinuxCommand',
    'input_manufacturer': 'Mycodo',
    'common_name_input': 'Linux Command',
    'common_name_measurements': 'Return Value',
    'unique_name_measurements': [],  # List of strings
    'dependencies_pypi': ['smbus'],  # List of strings
    'interfaces': ['Mycodo'],  # List of strings
    'cmd_command': 'shuf -i 50-70 -n 1',
    'cmd_measurement': 'Condition',
    'cmd_measurement_units': 'unit',
    'options_enabled': ['period', 'cmd_command', 'cmd_measurement_units', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface']
}


class InputModule(AbstractInput):
    """ A sensor support class that returns a value from a command """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.linux_command")
        self._measurement = None
        self.cmd_measurement = 'measurement'

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.linux_command_{id}".format(id=input_dev.id))
            self.cmd_command = input_dev.cmd_command
            self.cmd_measurement = input_dev.measurements

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
            self.logger.error(
                "The command returned a non-numerical value. "
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
