# coding=utf-8
import logging

import os

from mycodo.databases.models import DeviceMeasurements
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.database import db_retrieve_table_daemon

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
    'input_manufacturer': 'System',
    'input_name': 'CPU Load',
    'measurements_name': 'CPULoad',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'measurements_select',
        'period',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['Mycodo'],
    'location': {
        'title': 'Directory',
        'phrase': 'Directory to report the free space of',
        'options': [('/', '')]
    }
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the raspberry pi's cpu load """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.setup_logger(testing=testing, name=__name__, input_dev=input_dev)
        self._cpu_load_1m = None
        self._cpu_load_5m = None
        self._cpu_load_15m = None

        if not testing:
            self.device_measurements = db_retrieve_table_daemon(
                DeviceMeasurements).filter(
                    DeviceMeasurements.device_id == input_dev.unique_id)

    def get_measurement(self):
        """ Gets the cpu load averages """
        self.return_dict = measurements_dict.copy()

        load_avg = os.getloadavg()

        if self.is_enabled(0):
            self.set_value(0, load_avg[0])

        if self.is_enabled(1):
            self.set_value(1, load_avg[1])

        if self.is_enabled(2):
            self.set_value(2, load_avg[2])

        return self.return_dict
