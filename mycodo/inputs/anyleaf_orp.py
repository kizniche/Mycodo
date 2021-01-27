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
        ('apt', 'python3-numpy', 'python3-numpy'),
        ('apt', 'python3-scipy', 'python3-scipy'),
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit_Extended_Bus'),
        ('pip-pypi', 'anyleaf', 'anyleaf')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x48', '0x49'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'cal_v',
            'type': 'float',
            'default_value': 0.4,
            'name': "{}: {} ({})".format(lazy_gettext('Calibrate'), lazy_gettext('Voltage'), lazy_gettext('Internal')),
            'phrase': 'Calibration data: internal voltage'
        },
        {
            'id': 'cal_orp',
            'type': 'float',
            'default_value': 400.0,
            'name': "{}: {} ({})".format(lazy_gettext('Calibrate'), lazy_gettext('ORP'), lazy_gettext('Internal')),
            'phrase': 'Calibration data: internal ORP'
        },
    ],
    'custom_actions_message': """Calibrate: Place your probe in a solution of known ORP. Set 
the known ORP value in the `Calibration ORP` field, and press `Calibrate`. You don't need to change
 the values under `Custom Options`.""",
    'custom_actions': [
        {
            'id': 'calibration_orp',
            'type': 'float',
            'default_value': 400.0,
            'name': "{}: {} ({})".format(lazy_gettext('Calibrate'), lazy_gettext('Buffer ORP'), lazy_gettext('mV')) ,
            'phrase': 'This is the nominal ORP of the calibration buffer in mV, usually labelled on the bottle.'
        },
        {
            'id': 'calibrate',
            'type': 'button',
            'name': lazy_gettext('Calibrate'),
        },
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors AnyLeaf sensor pH or ORP"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

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

        # `default_value` above doesn't set the default in the database: custom options will initialize to None.
        if self.get_custom_option("cal_v"):
            cal_v = self.get_custom_option("cal_v")
        else:
            cal_v = 0.4
        if self.get_custom_option("cal_orp"):
            cal_orp = self.get_custom_option("cal_orp")
        else:
            cal_orp = 400.0

        # Load cal data from the database.
        self.sensor.calibrate_all(CalPtOrp(
            cal_v,
            cal_orp,
        ))

    def calibrate(self, args_dict):
        """ Auto-calibrate """
        if 'calibration_orp' not in args_dict:
            self.logger.error("Cannot conduct calibration without a buffer ORP value")
            return
        if not isinstance(args_dict['calibration_orp'], float) and not isinstance(args_dict['calibration_orp'], int):
            self.logger.error("buffer value does not represent a number: '{}', type: {}".format(
                args_dict['calibration_orp'], type(args_dict['calibration_orp'])))
            return
        
        v = self.sensor.calibrate(args_dict['calibration_orp'])  # For this session

        # For future sessions
        self.set_custom_option("cal_orp", args_dict['calibration_orp'])
        self.set_custom_option("cal_v", v)

    def get_measurement(self):
        """ Gets the measurement """
        self.return_dict = copy.deepcopy(measurements_dict)

        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.logger.error("PRE")
        self.value_set(0, self.sensor.read())

        self.logger.error("F", self.sensor.read(), self.sensor)

        return self.return_dict
