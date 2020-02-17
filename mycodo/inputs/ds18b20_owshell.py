# coding=utf-8
import subprocess
import time

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

    'options_enabled': [
        'location',
        'resolution',
        'period',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'ow-shell', 'ow-shell')
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
    """ A sensor support class that monitors the DS18B20's temperature """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        if not testing:
            self.location = input_dev.location
            self.resolution = input_dev.resolution

    def get_measurement(self):
        """ Gets the DS18B20's temperature in Celsius """
        self.return_dict = measurements_dict.copy()

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
                    command = 'owread /{id}/{temp}; echo'.format(
                        id=self.location,
                        temp=str_temperature)
                    owread = subprocess.Popen(
                        command, stdout=subprocess.PIPE, shell=True)
                    (owread_output, _) = owread.communicate()
                    owread.wait()
                    if owread_output:
                        temperature = float(owread_output.decode("latin1"))
                except Exception:
                    self.logger.exception(1)
            except Exception as e:
                if i == n:
                    self.logger.exception(
                        "{cls} raised an exception when taking a reading: "
                        "{err}".format(cls=type(self).__name__, err=e))
                time.sleep(1)

        if temperature == 85:
            self.logger.error(
                "Measurement returned 85 C, "
                "indicating an issue communicating with the sensor.")
            return None
        elif temperature is not None and not -55 < temperature < 125:
            self.logger.error(
                "Measurement outside the expected range of -55 C to 125 C: "
                "{temp} C".format(temp=temperature))
            return None

        self.value_set(0, temperature)

        return self.return_dict
