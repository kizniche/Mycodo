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
        'measurement': 'pH',
        'unit': 'pH'
    },
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ANYLEAF_PH',
    'input_manufacturer': 'AnyLeaf',
    'input_name': 'AnyLeaf pH',
    'input_library': '',
    'measurements_name': 'pH',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://anyleaf.org/ph-module',
    'url_datasheet': 'https://anyleaf.org/static/ph-module-datasheet.pdf',

    'options_enabled': [
        'i2c_location',
        'period',
    ],
    'options_disabled': [],

    'dependencies_module': [
        ('pip-pypi', 'anyleaf', 'anyleaf')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x48', '0x49'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'cal_0',
            'type': 'tuple',
            'default_value': (0.18, 4., 23.),
            'required': False,
            'name': lazy_gettext('Cal Pt 0'),
            'phrase': lazy_gettext('First Cal pt: Voltage, pH, Temperature')
        },
                {
            'id': 'cal_1',
            'type': 'tuple',
            'default_value': (0, 7., 23.),
            'required': False,
            'name': lazy_gettext('Cal Pt 0'),
            'phrase': lazy_gettext('Second Cal pt: Voltage, pH, Temperature')
        },
        {
            'id': 'cal_2',
            'type': 'tuple',
            'default_value': (-0.18, 10., 23.),
            'required': False,
            'name': lazy_gettext('Cal Pt 0'),
            'phrase': lazy_gettext('Third Cal pt: Voltage, pH, Temperature')
        }
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
        
        from anyleaf import PhSensor, CalPt, CalSlot, OnBoard, OffBoard

        self.sensor = PhSensor(i2c, self.period)

        # todo: Calibration


    def get_measurement(self):
        """ Gets the measurement """
        if not self.sensor:
            self.logger.error("Input not set up")
            return


        self.value_set(0, self.sensor.read(OnBoard()))
       

        return self.return_dict

