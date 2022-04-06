# coding=utf-8
import copy
import os

from mycodo.config_translations import TRANSLATIONS
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
    'input_name_short': 'Open Port',
    'input_library': 'nc',
    'measurements_name': 'Boolean',
    'measurements_dict': measurements_dict,

    'message': 'This Input executes the bash command "nc -zv [host] [port]" to determine if the host at a particular port is accessible.',

    'options_enabled': [
        'location',
        'port',
        'period',
        'pre_output'
    ],

    'location': {
        'name': TRANSLATIONS["host"]["title"],
        'phrase': TRANSLATIONS["host"]["phrase"],
        'options': [('127.0.0.1', '')]
    },
    'port': 80
}


class InputModule(AbstractInput):
    """
    A sensor support class that pings a server and returns 1 if it's up and 0 if it's down.
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.location = None
        self.port = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.location = self.input_dev.location
        self.port = self.input_dev.port

    def get_measurement(self):
        """Determine if the return value of the command is a number."""
        self.return_dict = copy.deepcopy(measurements_dict)

        response = os.system("nc -zv {host} {port} > /dev/null 2>&1".format(
            port=self.port,  host=self.location))

        if response == 0:
            self.value_set(0, 1)
        else:
            self.value_set(0, 0)

        return self.return_dict
