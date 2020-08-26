# coding=utf-8

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput


def constraints_pass_positive_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


# Measurements
measurements_dict = {
    0: {
        'measurement': 'ORP',
        'unit': 'mV'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ANYLEAF_ORP',
    'input_manufacturer': 'AnyLeaf',
    'input_name': 'AnyLeaf ORP',
    'input_library': '',
    'measurements_name': 'ORP',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://anyleaf.org/ph-module',
    'url_datasheet': 'https://anyleaf.org/static/ph-module-datasheet.pdf',

    'message': 'Calibration Measurement is an optional setting that provides a temperature measurement (in Celsius) of the water that the pH is being measured from.',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
    ],
    'options_disabled': [],

    'dependencies_module': [
        ('pip-pypi', 'anyleaf')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x48', '0x49'],
    'i2c_address_editable': False,

    'custom_options': [

    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors AnyLeaf sensor pH or ORP"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None


    def initialize_input(self):
        # todo: This module can be connected to either a pH probe or ORP. Should
        # that bet set up with both here, or as two separate files?
        
        from anyleaf import OrpSensor, CalPtOrp

        self.sensor = OrpSensor(i2c, self.period)

        # todo: Calibration


    def get_measurement(self):
        """ Gets the measurement """
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.value_set(0, self.sensor.read()

        return self.return_dict

