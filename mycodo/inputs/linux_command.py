# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
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
    'input_manufacturer': 'Linux',
    'input_name': 'Bash Command',
    'measurements_name': 'Return Value',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'custom_options',
        'measurements_select_measurement_unit',
        'period',
        'cmd_command',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'enable_channel_unit_select': True,
    'interfaces': ['Mycodo'],
    'cmd_command': 'shuf -i 50-70 -n 1',

    'custom_options': [
        {
            'id': 'command_timeout',
            'type': 'integer',
            'default_value': 60,
            'required': True,
            'name': lazy_gettext('Command Timeout'),
            'phrase': lazy_gettext('How long to wait for the command to finish before killing the process.')
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that returns a value from a command """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            self.command = input_dev.cmd_command
            self.command_timeout = None
            if input_dev.custom_options:
                for each_option in input_dev.custom_options.split(';'):
                    option = each_option.split(',')[0]
                    value = each_option.split(',')[1]
                    if option == 'command_timeout':
                        self.command_timeout = int(value)

    def get_measurement(self):
        """ Determine if the return value of the command is a number """
        self.return_dict = measurements_dict.copy()

        self.logger.debug("Command being executed: {}".format(self.command))

        timeout = 360
        if self.command_timeout:
            timeout = self.command_timeout

        out, err, status = cmd_output(self.command, timeout=timeout)

        self.logger.debug("Command returned: Status: {}, Error: {}".format(err, status))

        if str_is_float(out):
            list_measurements = [float(out)]
        else:
            self.logger.error(
                "The command returned a non-numerical value. "
                "Ensure only one numerical value is returned "
                "by the command. Value returned: '{}'".format(out))
            return

        for channel in self.channels_measurement:
            if self.is_enabled(channel):
                self.return_dict[channel]['unit'] = self.channels_measurement[channel].unit
                self.return_dict[channel]['measurement'] = self.channels_measurement[channel].measurement
                self.return_dict[channel]['value'] = list_measurements[channel]

        return self.return_dict
