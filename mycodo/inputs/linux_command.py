# coding=utf-8
import traceback

import copy
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

    'message': 'This Input will execute a command in the shell and store the output as a float value. Perform any unit conversions within your script or command. A measurement/unit is required to be selected.',

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

    'custom_options': [
        {
            'id': 'command_timeout',
            'type': 'integer',
            'default_value': 60,
            'required': True,
            'name': lazy_gettext('Command Timeout'),
            'phrase': 'How long to wait for the command to finish before killing the process.'
        },
        {
            'id': 'execute_as_user',
            'type': 'text',
            'default_value': 'mycodo',
            'required': True,
            'name': lazy_gettext('User'),
            'phrase': 'The user to execute the command'
        },
        {
            'id': 'current_working_dir',
            'type': 'text',
            'default_value': '/home/pi',
            'required': True,
            'name': lazy_gettext('Current Working Directory'),
            'phrase': 'The current working directory of the shell environment.'
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that returns a value from a command """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.command = None

        self.command_timeout = None
        self.execute_as_user = None
        self.current_working_dir = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        self.command = self.input_dev.cmd_command

    def get_measurement(self):
        """ Determine if the return value of the command is a number """
        self.return_dict = copy.deepcopy(measurements_dict)

        self.logger.debug("Command being executed: {}".format(self.command))

        timeout = 360
        if self.command_timeout:
            timeout = self.command_timeout

        try:
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
        except:
            self.logger.debug("Exception: {}".format(traceback.format_exc()))
