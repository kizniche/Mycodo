# coding=utf-8
import resource

from mycodo.inputs.base_input import AbstractInput
from mycodo.mycodo_client import DaemonControl

# Measurements
measurements_dict = {
    0: {
        'measurement': 'disk_space',
        'unit': 'MB'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name': 'Mycodo RAM',
    'input_name_unique': 'MYCODO_RAM',
    'input_manufacturer': 'Mycodo',
    'measurements_name': 'Size RAM in Use',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'period'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['Mycodo']
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures ram used by the Mycodo daemon

    """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self._disk_space = None

        if not testing:
            self.control = DaemonControl()

    def get_measurement(self):
        """ Gets the measurement in units by reading resource """
        self.return_dict = measurements_dict.copy()

        try:
            self.value_set(0, resource.getrusage(
                resource.RUSAGE_SELF).ru_maxrss / float(1000))
            return self.return_dict
        except Exception:
            pass
