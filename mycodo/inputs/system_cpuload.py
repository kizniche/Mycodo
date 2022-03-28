# coding=utf-8
import copy
import os

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'cpu_load_1m',
        'unit': 'cpu_load'
    },
    1: {
        'measurement': 'cpu_load_5m',
        'unit': 'cpu_load'
    },
    2: {
        'measurement': 'cpu_load_15m',
        'unit': 'cpu_load'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'RPiCPULoad',
    'input_manufacturer': 'Mycodo',
    'input_name': 'CPU Load',
    'input_library': 'os.getloadavg()',
    'measurements_name': 'CPULoad',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'measurements_select',
        'period'
    ],

    'location': {
        'title': 'Directory',
        'phrase': 'Directory to report the free space of',
        'options': [('/', '')]
    }
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the raspberry pi's cpu load."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

    def get_measurement(self):
        """Gets the cpu load averages."""
        self.return_dict = copy.deepcopy(measurements_dict)

        load_avg = os.getloadavg()
        self.value_set(0, load_avg[0])
        self.value_set(1, load_avg[1])
        self.value_set(2, load_avg[2])

        return self.return_dict
