# coding=utf-8

import copy
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
        'measurement': 'oxidation_reduction_potential',
        'unit': 'mV'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ANYLEAF_ORP',
    'input_manufacturer': 'AnyLeaf',
    'input_name': 'AnyLeaf ORP',
    'input_library': 'anyleaf',
    'measurements_name': 'Oxidation Reduction Potential',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://anyleaf.org/ph-module',
    'url_datasheet': 'https://anyleaf.org/static/ph-module-datasheet.pdf',

    'options_enabled': [
        'i2c_location',
        'period',
    ],
    'options_disabled': [],

    'dependencies_module': [
        ('pip-pypi', 'anyleaf', 'anyleaf'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit_Extended_Bus')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x48', '0x49'],
    'i2c_address_editable': False,

    'custom_options': [
    #    {
    #         'id': 'cal_1_V',
    #         'type': 'float',
    #         'default_value': (400.),
    #         'required': False,
    #         'name': lazy_gettext('Cal Pt 0'),
    #         'phrase': lazy_gettext('Calibration: Voltage (V)')
    #     },
    #     {
    #         'id': 'cal_1_pH',
    #         'type': 'float',
    #         'default_value': (0.4),
    #         'required': False,
    #         'name': lazy_gettext('Cal Pt 0'),
    #         'phrase': lazy_gettext('Calibration: ORP (mV)')
    #     },
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors AnyLeaf sensor pH or ORP"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.cal = None

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        from adafruit_extended_bus import ExtendedI2C
        from anyleaf import OrpSensor, CalPtOrp

        self.sensor = OrpSensor(
            ExtendedI2C(self.input_dev.i2c_bus),
            self.input_dev.period,
            address=int(str(self.input_dev.i2c_location), 16)
        )

        # todo: Calibration
        
    def get_measurement(self):
        """ Gets the measurement """
        self.return_dict = copy.deepcopy(measurements_dict)

        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.value_set(0, self.sensor.read())

        return self.return_dict

