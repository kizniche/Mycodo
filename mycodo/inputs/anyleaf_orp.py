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
    ],
    'custom_actions_message': 'Calibrate',
    'custom_actions': [
        {
            'id': 'calibration_orp',
            'type': 'float',
            'default_value': 400.,
            'name': lazy_gettext('Calibration buffer ORP (mV)'),
            'phrase': 'This is the nominal ORP of the calibration buffer in mV, usually labelled on the bottle.'
        },
        {
            'id': 'calibrate',
            'type': 'button',
            'name': lazy_gettext('Calibrate')
        },
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

        self.cal = CalPtOrp(0.4, 400.0)


    def calibrate(self, args_dict):
        """ Auto-calibrate """
        from anyleaf import CalPtOrp
        
        if 'calibration_orp' not in args_dict:
            self.logger.error("Cannot conduct calibration without a buffer ORP value")
            return
            if not isinstance(args_dict['calibration_orp'], float) and not isinstance(args_dict['calibration_orp'], int):
                self.logger.error("buffer value does not represent a number: '{}', type: {}".format(
                    args_dict['calibration_orp'], type(args_dict['calibration_orp'])))
                return

        self.cal = CalPtOrp(
            self.sensor.read_voltage(),
            args_dict['calibration_orp'],
        )

    def get_measurement(self):
        """ Gets the measurement """
        self.return_dict = copy.deepcopy(measurements_dict)

        if not self.sensor:
            self.logger.error("Input not set up")
            return

        # Calibrate each time, since calibration values held in this class remain, while
        # ones held in `this.sensor` are periodically re-initialized.
        # todo: Still loses all cal data on deactivation.
        self.sensor.calibrate_all(self.cal)

        self.value_set(0, self.sensor.read())

        return self.return_dict

