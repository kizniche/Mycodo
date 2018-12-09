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
    'input_name_unique': 'SERVER_PORT_OPEN',
    'input_manufacturer': 'Mycodo',
    'input_name': 'Server Port Open',
    'measurements_name': 'Boolean',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'location',
        'port',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['Mycodo'],
    'location': {
        'title': 'Host Location',
        'phrase': 'Host name or IP address',
        'options': [('127.0.0.1', '')]
    },
    'port': 80
}


class InputModule(AbstractInput):
    """
    A sensor support class that pings a server and returns 1 if it's up
    and 0 if it's down.
    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.server_port_open")
        self._measurement = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.server_port_open_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.location = input_dev.location
            self.port = input_dev.port

    def get_measurement(self):
        """ Determine if the return value of the command is a number """
        return_dict = measurements_dict.copy()

        response = os.system(
            "nc -zv {host} {port} > /dev/null 2>&1".format(
                port=self.port,  host=self.location))

        if response == 0:
            return_dict[0]['value'] = 1
        else:
            return_dict[0]['value'] = 0

        return return_dict
