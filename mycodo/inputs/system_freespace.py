# coding=utf-8
import os

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'disk_space',
        'unit': 'MB'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'RPiFreeSpace',
    'input_manufacturer': 'System',
    'input_name': 'Free Space',
    'measurements_name': 'Unallocated Disk Space',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'location',
        'period',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['Mycodo'],
    'location': {
        'title': 'Path',
        'phrase': 'The path to monitor the free space of',
        'options': [('/', '')]
    }
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the free space of a path """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self._disk_space = None

        if not testing:
            self.path = input_dev.location

    def get_measurement(self):
        """ Gets the free space """
        self.return_dict = measurements_dict.copy()

        f = os.statvfs(self.path)
        self.value_set(0, (f.f_bsize * f.f_bavail) / 1000000.0)

        return self.return_dict
