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
        'measurement': 'ion_concentration',
        'unit': 'pH'
    },
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ANYLEAF_PH',
    'input_manufacturer': 'AnyLeaf',
    'input_name': 'AnyLeaf pH',
    'input_library': 'anyleaf',
    'measurements_name': 'Ion concentration',
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
        {
            'id': 'temp_source',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math'
            ],
            'name': lazy_gettext('Temperature compensation source. Leave at `Select one` to use the onboard sensor.'),
            'phrase': lazy_gettext('Select a measurement for temperature compensation. If not selected, uses the onboard sensor.')
        },
        # {
        #     'id': 'cal_1_V',
        #     'type': 'float',
        #     'default_value': (0.18),
        #     'required': False,
        #     'name': lazy_gettext('Cal Pt 0'),
        #     'phrase': lazy_gettext('1st Cal pt: Voltage')
        # },
        # {
        #     'id': 'cal_1_pH',
        #     'type': 'float',
        #     'default_value': (4.),
        #     'required': False,
        #     'name': lazy_gettext('Cal Pt 0'),
        #     'phrase': lazy_gettext('1st Cal pt: pH')
        # },
        # {
        #     'id': 'cal_1_T',
        #     'type': 'float',
        #     'default_value': (23.),
        #     'required': False,
        #     'name': lazy_gettext('Cal Pt 0'),
        #     'phrase': lazy_gettext('1st Cal pt: Temperature (°C)')
        # },
        #         {
        #     'id': 'cal_1_V',
        #     'type': 'float',
        #     'default_value': (0.),
        #     'required': False,
        #     'name': lazy_gettext('Cal Pt 0'),
        #     'phrase': lazy_gettext('2nd Cal pt: Voltage')
        # },
        # {
        #     'id': 'cal_1_pH',
        #     'type': 'float',
        #     'default_value': (7.),
        #     'required': False,
        #     'name': lazy_gettext('Cal Pt 0'),
        #     'phrase': lazy_gettext('2nd Cal pt: pH')
        # },
        # {
        #     'id': 'cal_1_T',
        #     'type': 'float',
        #     'default_value': (23.),
        #     'required': False,
        #     'name': lazy_gettext('Cal Pt 0'),
        #     'phrase': lazy_gettext('2nd Cal pt: Temperature (°C)')
        # },
        #         {
        #     'id': 'cal_3_V',
        #     'type': 'float',
        #     'default_value': (-0.18),
        #     'required': False,
        #     'name': lazy_gettext('Cal Pt 0'),
        #     'phrase': lazy_gettext('3rd Cal pt: Voltage')
        # },
        # {
        #     'id': 'cal_3_pH',
        #     'type': 'float',
        #     'default_value': (10.),
        #     'required': False,
        #     'name': lazy_gettext('Cal Pt 0'),
        #     'phrase': lazy_gettext('3rd Cal pt: pH')
        # },
        # {
        #     'id': 'cal_3_T',
        #     'type': 'float',
        #     'default_value': (23.),
        #     'required': False,
        #     'name': lazy_gettext('Cal Pt 0'),
        #     'phrase': lazy_gettext('3rd Cal pt: Temperature (°C)')
        # },
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors AnyLeaf sensor pH or ORP"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.temp_source = None
        self.cal_1 = None
        self.cal_2 = None
        self.cal_3 = None

        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        from adafruit_extended_bus import ExtendedI2C
        from anyleaf import PhSensor, CalPt, CalSlot

        self.sensor = PhSensor(
            ExtendedI2C(self.input_dev.i2c_bus),
            self.input_dev.period,
            address=int(str(self.input_dev.i2c_location), 16)
        )
        

        # todo: Calibration
        # todo: temperature compensation

    # def calibrate(self):
    #     """ Auto-calibrate """
    #     if not self.sensor:
    #         self.logger.error("Input not set up")
    #         return


    #     self.value_set(0, self.sensor.read(OnBoard()))
       

    #     return self.return_dict


    def get_measurement(self):
        """ Gets the measurement """
        from anyleaf import OnBoard, OffBoard
        self.return_dict = copy.deepcopy(measurements_dict)

        if not self.sensor:
            self.logger.error("Input not set up")
            return

        # if self.input_dev.temp_source:
            # self.value_set(0, self.sensor.read(OffBoard(self.input_dev.temp_source.get_last_measurement())))
        # else:
        self.value_set(0, self.sensor.read(OnBoard()))
       

        return self.return_dict

