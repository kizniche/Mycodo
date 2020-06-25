# coding=utf-8
import subprocess
import time

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput


def constraints_pass_measure_range(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: str
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure valid range is selected
    if value not in ['w1thermsensor', 'ow_shell']:
        all_passed = False
        errors.append("Invalid range")
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'DS18S20',
    'input_manufacturer': 'MAXIM',
    'input_name': 'DS18S20',
    'input_library': 'w1thermsensor',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.maximintegrated.com/en/products/sensors/DS18S20.html',
    'url_datasheet': 'https://datasheets.maximintegrated.com/en/ds/DS18S20.pdf',

    'options_enabled': [
        'location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'w1thermsensor', 'w1thermsensor'),
    ],

    'interfaces': ['1WIRE']
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the DS18S20's temperature """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        # Initialize custom options
        self.library = None
        # Set custom options
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            from w1thermsensor import W1ThermSensor

            self.location = input_dev.location

            if self.library == 'w1thermsensor':
                self.sensor = W1ThermSensor(
                    W1ThermSensor.THERM_SENSOR_DS18S20, self.location)
            elif self.library == 'ow_shell':
                # TODO: Remove ow-shell from this module as a new module for ow-shell has been created.
                pass

    def get_measurement(self):
        """ Gets the DS18S20's temperature in Celsius """
        self.return_dict = measurements_dict.copy()

        n = 2
        for i in range(n):
            try:
                if self.library == 'w1thermsensor':
                    self.value_set(0, self.sensor.get_temperature())
                elif self.library == 'ow_shell':
                    try:
                        command = 'owread /{id}/temperature; echo'.format(
                            id=self.location)
                        owread = subprocess.Popen(
                            command, stdout=subprocess.PIPE, shell=True)
                        (owread_output, _) = owread.communicate()
                        owread.wait()
                        if owread_output:
                            self.value_set(0, float(owread_output.decode("latin1")))
                    except Exception:
                        self.logger.exception(1)
                return self.return_dict
            except Exception as e:
                if i == n:
                    self.logger.exception(
                        "{cls} raised an exception when taking a reading: "
                        "{err}".format(cls=type(self).__name__, err=e))
                time.sleep(1)
