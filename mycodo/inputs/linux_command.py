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
        },
        {
            'id': 'execute_as_user',
            'type': 'text',
            'default_value': 'pi',
            'required': True,
            'name': lazy_gettext('User'),
            'phrase': lazy_gettext('The user to execute the command.')
        },
        {
            'id': 'current_working_dir',
            'type': 'text',
            'default_value': '/home/pi',
            'required': True,
            'name': lazy_gettext('CWD'),
            'phrase': lazy_gettext('The current working directory of the shell environment.')
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that returns a value from a command """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        # custom options
        self.command_timeout = None
        self.execute_as_user = None
        self.current_working_dir = None
        # set custom_options
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.command = input_dev.cmd_command

    def get_measurement(self):
        """ Determine if the return value of the command is a number """
        self.return_dict = measurements_dict.copy()

        self.logger.debug("Command being executed: {}".format(self.command))

        timeout = 360
        if self.command_timeout:
            timeout = self.command_timeout

        out, err, status = cmd_output(
            self.command,
            timeout=timeout,
            user=self.execute_as_user,
            cwd=self.current_working_dir)

        self.logger.debug("Command returned: {}, Status: {}, Error: {}".format(out, err, status))

        if str_is_float(out):
            measurement_value = float(out)
        else:
            self.logger.debug(
                "The command returned a non-numerical value. "
                "Ensure only one numerical value is returned "
                "by the command. Value returned: '{}'".format(out))
            return

        for channel in self.channels_measurement:
            if self.is_enabled(channel):
                self.return_dict[channel]['unit'] = self.channels_measurement[channel].unit
                self.return_dict[channel]['measurement'] = self.channels_measurement[channel].measurement
                self.return_dict[channel]['value'] = measurement_value

        return self.return_dict
