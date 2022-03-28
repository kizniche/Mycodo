# coding=utf-8
import copy

from mycodo.config import MYCODO_VERSION
from mycodo.inputs.base_input import AbstractInput
from mycodo.mycodo_client import DaemonControl

# Measurements
measurements_dict = {
    0: {
        'measurement': 'version',
        'unit': 'unitless',
        'name': 'Major'
    },
    1: {
        'measurement': 'version',
        'unit': 'unitless',
        'name': 'Minor'
    },
    2: {
        'measurement': 'version',
        'unit': 'unitless',
        'name': 'Revision'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name': 'Mycodo Version',
    'input_name_unique': 'MYCODO_VERSION',
    'input_manufacturer': 'Mycodo',
    'measurements_name': 'Version as Major.Minor.Revision',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'period',
        'measurements_select'
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

        try:
            version = MYCODO_VERSION.split('.')
            self.value_set(0, int(version[0]))
            self.value_set(1, int(version[1]))
            self.value_set(2, int(version[2]))

            return self.return_dict
        except Exception:
            pass
