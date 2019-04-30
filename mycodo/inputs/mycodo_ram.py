# coding=utf-8
import logging
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
        'period',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['Mycodo']
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures ram used by the Mycodo daemon

    """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.mycodo_ram")
        self._disk_space = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.mycodo_ram_{id}".format(id=input_dev.unique_id.split('-')[0]))

            self.control = DaemonControl()

        if input_dev.log_level_debug:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def get_measurement(self):
        """ Gets the measurement in units by reading resource """
        return_dict = measurements_dict.copy()

        try:
            return_dict[0]['value'] = resource.getrusage(
                resource.RUSAGE_SELF).ru_maxrss / float(1000)
            return return_dict
        except Exception:
            pass
