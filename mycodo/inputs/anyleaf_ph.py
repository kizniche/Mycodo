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
    ],
    'custom_actions_message': 'Calibrate: Place your probe in a buffer of ...', # todo
    'custom_actions': [
        {
            'id': 'calibration_ph',
            'type': 'float',
            'default_value': 7.,
            'name': lazy_gettext('Calibration buffer pH'),
            'phrase': 'This is the nominal pH of the calibration buffer, usually labelled on the bottle.'
        },
        {
            'id': 'calibrate_slot_1',
            'type': 'button',
            'name': lazy_gettext('Calibrate, slot 1')
        },
        {
            'id': 'calibrate_slot_2',
            'type': 'button',
            'name': lazy_gettext('Calibrate, slot 2')
        },
        {
            'id': 'calibrate_slot_3',
            'type': 'button',
            'name': lazy_gettext('Calibrate, slot 3')
        },
        # todo: Including this input will raise an error about `cannot convert string to float`
        # todo when attempting calibration.
        # {
        #     'id': 'temperature_comp_meas',
        #     'type': 'select_measurement',
        #     'default_value': '',
        #     'options_select': [
        #         'Input',
        #         'Math'
        #     ],
        #     'name': lazy_gettext('Temperature Compensation Measurement'),
        #     'phrase': lazy_gettext('Select a measurement for temperature compensation')
        # },
        {
            'id': 'max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Temperature Compensation Max Age'),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use for temperature compensation')
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors AnyLeaf sensor pH or ORP"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.temperature_comp_meas_device_id = None
        self.temperature_comp_meas_measurement_id = None
        self.max_age = None
        self.cal_1 = None
        self.cal_2 = None
        self.cal_3 = None

        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        from adafruit_extended_bus import ExtendedI2C
        from anyleaf import PhSensor

        self.sensor = PhSensor(
            ExtendedI2C(self.input_dev.i2c_bus),
            self.input_dev.period,
            address=int(str(self.input_dev.i2c_location), 16)
        )

        self.cal_1 = CalPt(0, 7.0, 23.)
        self.cal_2 = CalPt(0.17, 4.0, 23.)
        self.cal_3 = None

    def calibrate(self, cal_slot, args_dict):
        """Calibration helper method"""
        self.logger.error("AA")

        from anyleaf import CalPt, CalSlot

        if 'calibration_ph' not in args_dict:
            self.logger.error("Cannot conduct calibration without a buffer pH value")
            return
        if not isinstance(args_dict['calibration_ph'], float) and not isinstance(args_dict['calibration_ph'], int):
            self.logger.error("buffer value does not represent a number: '{}', type: {}".format(
                args_dict['calibration_ph'], type(args_dict['calibration_ph'])))
            return

        pt = CalPt(
            self.sensor.read_voltage(),
            args_dict['calibration_ph'],
            self.sensor.read_temp(), # todo offboard
        )

        if cal_slot == CalSlot.ONE:
            self.cal_1 = pt
        elif cal_slot == CalSlot.TWO:
            self.cal_2 = pt
        else:
            self.cal_3 = pt

    def calibrate_slot_1(self, args_dict):
        # """ Auto-calibrate """
        # # todo: You probably need to store in this class, not self.sensor, to avoid it
        # # todo resetting. experiment.

        from anyleaf import CalSlot
        self.calibrate(CalSlot.ONE, args_dict)

    def calibrate_slot_2(self, args_dict):
        """ Auto-calibrate """

        from anyleaf import CalSlot
        self.calibrate(CalSlot.TWO, args_dict)

    def calibrate_slot_3(self, args_dict):
        # """ Auto-calibrate """

        from anyleaf import CalSlot
        self.calibrate(CalSlot.THREE, args_dict)

    def get_measurement(self):
        """ Gets the measurement """
        from anyleaf import OnBoard, OffBoard
        self.return_dict = copy.deepcopy(measurements_dict)

        if not self.sensor:
            self.logger.error("Input not set up")
            return

        # Calibrate each time, since calibration values held in this class remain, while
        # ones held in `this.sensor` are periodically re-initialized.
        # todo: Still loses all cal data on deactivation.
        self.sensor.calibrate_all(self.cal_1, self.cal_2, self.cal_3)

        # todo: Test offboard temp compensation.
        if self.temperature_comp_meas_measurement_id:
            last_temp_measurement = self.get_last_measurement(
                self.temperature_comp_meas_device_id,
                self.temperature_comp_meas_measurement_id,
                max_age=self.max_age
            )

            if last_temp_measurement:
                temp_data = OffBoard(last_temp_measurement[1])
            else:
            temp_data = OnBoard()

        else:
            temp_data = OnBoard()

        self.value_set(0, self.sensor.read(temp_data))

        return self.return_dict

