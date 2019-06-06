# coding=utf-8
import logging

import os

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'boolean',
        'unit': 'bool'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SERVER_PING',
    'input_manufacturer': 'System',
    'input_name': 'Server Ping',
    'measurements_name': 'Boolean',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'location',
        'times_check',
        'deadline',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['Mycodo'],
    'location': {
        'title': 'Host Location',
        'phrase': 'Host name or IP address',
        'options': [('127.0.0.1', '')]
    },
    'times_check': 1,
    'deadline': 2
}


class InputModule(AbstractInput):
    """
    A sensor support class that pings a server and returns 1 if it's up
    and 0 if it's down.
    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, name=__name__)

        if not testing:
            self.location = input_dev.location
            self.times_check = input_dev.times_check
            self.deadline = input_dev.deadline

    def get_measurement(self):
        """ Determine if the return value of the command is a number """
        self.return_dict = measurements_dict.copy()

        response = os.system(
            "ping -c {times} -w {deadline} {host} > /dev/null 2>&1".format(
                times=self.times_check, deadline=self.deadline, host=self.location))

        if response == 0:
            self.set_value(0, 1)  # Server is up
        else:
            self.set_value(0, 0)  # Server is down

        return self.return_dict
