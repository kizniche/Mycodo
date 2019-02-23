# coding=utf-8
import logging

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import cmd_output
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements_dict = {
    0: {
        'measurement': '',
        'unit': ''
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'LinuxCommand',
    'input_manufacturer': 'Mycodo',
    'input_name': 'Linux Command',
    'measurements_name': 'Return Value',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'measurements_select_measurement_unit',
        'period',
        'cmd_command',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'enable_channel_unit_select': True,
    'interfaces': ['Mycodo'],
    'cmd_command': 'shuf -i 50-70 -n 1',
}


class InputModule(AbstractInput):
    """ A sensor support class that returns a value from a command """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.linux_command")

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.linux_command_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                DeviceMeasurements.device_id == input_dev.unique_id)

            self.command = input_dev.cmd_command

    def get_measurement(self):
        """ Determine if the return value of the command is a number """
        return_dict = measurements_dict.copy()

        out, _, _ = cmd_output(self.command)

        if str_is_float(out):
            list_measurements = [float(out)]
        else:
            self.logger.error(
                "The command returned a non-numerical value. "
                "Ensure only one numerical value is returned "
                "by the command.")
            return

        for channel, meas in enumerate(self.device_measurements.all()):
            if meas.is_enabled:
                return_dict[channel]['unit'] = meas.unit
                return_dict[channel]['measurement'] = meas.measurement
                return_dict[channel]['value'] = list_measurements[channel]

        return return_dict
