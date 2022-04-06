# coding=utf-8
import os.path
import subprocess

import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'CPU'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C',
        'name': 'GPU'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'RPi',
    'input_manufacturer': 'Raspberry Pi',
    'input_name': 'CPU/GPU Temperature',
    'input_name_short': 'CPU/GPU Temp',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': True,

    'message': 'The internal CPU and GPU temperature of the Raspberry Pi.',

    'options_enabled': [
        'measurements_select',
        'period'
    ],
    'options_disabled': ['interface'],

    'interfaces': ['RPi'],

    'custom_options': [
        {
            'id': 'path_temperature_cpu',
            'type': 'text',
            'default_value': '/sys/class/thermal/thermal_zone0/temp',
            'required': True,
            'name': "Path for CPU Temperature",
            'phrase': 'Reads the CPU temperature from this file'
        },
        {
            'id': 'path_temperature_gpu',
            'type': 'text',
            'default_value': '/usr/bin/vcgencmd',
            'required': True,
            'name': "Path to vcgencmd",
            'phrase': 'Reads the GPU from vcgencmd'
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the raspberry pi's CPU and GPU temperatures."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.path_temperature_cpu = None
        self.path_temperature_gpu = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)

    def get_measurement(self):
        """Gets the Raspberry pi's CPU and GPU temperatures."""
        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):  # CPU temperature
            if os.path.exists(self.path_temperature_cpu):
                try:
                    with open(self.path_temperature_cpu) as cpu_temp_file:
                        self.value_set(0, float(cpu_temp_file.read()) / 1000)
                        self.logger.debug("CPU Temperature: {}".format(self.value_get(0)))
                except Exception as err:
                    self.logger.error("Error getting CPU temperature: {}".format(err))
            else:
                self.logger.error("CPU temperature: could not locate {}".format(self.path_temperature_cpu))

        if self.is_enabled(1):  # GPU temperature
            if os.path.exists(self.path_temperature_gpu):
                try:
                    temperature_gpu = subprocess.check_output((self.path_temperature_gpu, 'measure_temp'))
                    self.value_set(1, float(temperature_gpu.split(b'=')[1].split(b"'")[0]))
                    self.logger.debug("GPU Temperature: {}".format(self.value_get(1)))
                except Exception as err:
                    self.logger.error("Error getting GPU temperature: {}".format(err))
            else:
                self.logger.error("GPU temperature: Could not locate {}".format(self.path_temperature_gpu))

        return self.return_dict
