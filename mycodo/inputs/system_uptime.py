# coding=utf-8
import copy
import os

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'duration_time',
        'unit': 's'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'INPUT_System_Uptime',
    'input_manufacturer': 'Mycodo',
    'input_name': 'Uptime',
    'input_library': '',
    'measurements_name': 'Seconds Since System Startup',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'period'
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that measures uptme."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

    def get_measurement(self):
        """Gets uptime"""
        if not os.path.exists('/proc/uptime'):
            self.logger.error("Cannot find path /proc/uptime")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        with open('/proc/uptime', 'r') as f:
            self.value_set(0, float(f.readline().split()[0]))

        return self.return_dict
