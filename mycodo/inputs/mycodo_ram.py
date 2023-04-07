# coding=utf-8
import copy
import resource

from mycodo.inputs.base_input import AbstractInput
from mycodo.mycodo_client import DaemonControl

# Measurements
measurements_dict = {
    0: {
        'measurement': 'disk_space',
        'unit': 'MB',
        'name': 'System RAM Free'
    },
    1: {
        'measurement': 'disk_space',
        'unit': 'MB',
        'name': 'System RAM Used'
    },
    2: {
        'measurement': 'disk_space',
        'unit': 'MB',
        'name': 'Mycodo Backend RAM Used'
    },
    3: {
        'measurement': 'disk_space',
        'unit': 'MB',
        'name': 'Mycodo Frontend RAM Used'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name': 'System and Mycodo RAM',
    'input_name_unique': 'MYCODO_RAM',
    'input_manufacturer': 'Mycodo',
    'input_library': 'psutil, resource.getrusage()',
    'measurements_name': 'RAM Allocation',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'period',
        'measurements_select'
    ],

    'dependencies_module': [
        ('pip-pypi', 'psutil', 'psutil==5.9.4')
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures ram used by the Mycodo daemon
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.control = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.control = DaemonControl()

    def get_measurement(self):
        """Gets the measurement in units by reading resource."""
        self.return_dict = copy.deepcopy(measurements_dict)

        import psutil

        try:
            system = psutil.virtual_memory()
            if self.is_enabled(0):
                self.value_set(0, system.available / (1024.0 ** 2))
            if self.is_enabled(1):
                self.value_set(1, system.used / (1024.0 ** 2))
        except:
            self.logger.exception("getting system ram")

        if self.is_enabled(2):
            self.value_set(2, self.control.ram_use())

        if self.is_enabled(3):
            try:
                import requests
                response = requests.get('https://127.0.0.1/ram', verify=False)
                self.value_set(3, float(response.content))
            except:
                self.logger.exception("getting frontend ram usage")

        return self.return_dict
