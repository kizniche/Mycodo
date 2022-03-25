# coding=utf-8
import subprocess
import time

import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'DS18B20_OWS',
    'input_manufacturer': 'MAXIM',
    'input_name': 'DS18B20',
    'input_library': 'ow-shell',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.maximintegrated.com/en/products/sensors/DS18B20.html',
    'url_datasheet': 'https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf',
    'url_product_purchase': [
        'https://www.adafruit.com/product/374',
        'https://www.adafruit.com/product/381',
        'https://www.sparkfun.com/products/245'
    ],
    'url_additional': 'https://github.com/cpetrich/counterfeit_DS18B20',

    'message': 'Warning: Counterfeit DS18B20 sensors are common and can cause a host of issues. Review the Additional '
               'URL for more information about how to determine if your sensor is authentic.',

    'options_enabled': [
        'location',
        'resolution',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'ow-shell', 'ow-shell'),
        ('apt', 'owfs', 'owfs')
    ],

    'interfaces': ['1WIRE'],
    'resolution': [
        ('', 'Use Chip Default'),
        (9, '9-bit, 0.5 °C, 93.75 ms'),
        (10, '10-bit, 0.25 °C, 187.5 ms'),
        (11, '11-bit, 0.125 °C, 375 ms'),
        (12, '12-bit, 0.0625 °C, 750 ms')
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the DS18B20's temperature."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.location = None
        self.resolution = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.location = self.input_dev.location
        self.resolution = self.input_dev.resolution

    def get_measurement(self):
        """Gets the DS18B20's temperature in Celsius."""
        self.return_dict = copy.deepcopy(measurements_dict)

        temperature = None
        n = 2
        for i in range(n):
            try:
                str_temperature = 'temperature'
                if self.resolution == 9:
                    str_temperature = 'temperature9'
                if self.resolution == 10:
                    str_temperature = 'temperature10'
                if self.resolution == 11:
                    str_temperature = 'temperature11'
                if self.resolution == 12:
                    str_temperature = 'temperature12'
                try:
                    command = 'owread /{id}/{temp}; echo'.format(id=self.location, temp=str_temperature)
                    self.logger.debug(f"Command: {command}")
                    owread = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
                    (owread_output, _) = owread.communicate()
                    owread.wait()
                    if owread_output:
                        self.logger.debug("Output: '{}'".format(owread_output))
                        temperature = float(owread_output.decode("latin1"))
                        break
                except Exception:
                    self.logger.exception("Obtaining measurement")
            except Exception as e:
                if i == n:
                    self.logger.exception(
                        "{cls} raised an exception when taking a reading: {err}".format(cls=type(self).__name__, err=e))
                time.sleep(1)

        if temperature == 85:
            self.logger.error("Measurement returned 85 C, indicating an issue communicating with the sensor.")
            return None
        elif temperature is not None and not -55 < temperature < 125:
            self.logger.error(
                "Measurement outside the expected range of -55 C to 125 C: {temp} C".format(temp=temperature))
            return None

        if temperature is not None:
            self.value_set(0, temperature)

        return self.return_dict
