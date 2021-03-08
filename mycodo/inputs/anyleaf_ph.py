# coding=utf-8
import copy

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
        # {
        #     'id': 'temp_source',
        #     'type': 'select_measurement',
        #     'default_value': '',
        #     'options_select': [
        #         'Input',
        #         'Function',
        #         'Math'
        #     ],
        #     'name': lazy_gettext('Temperature compensation source. Leave at `Select one` to use the onboard sensor.'),
        #     'phrase': lazy_gettext('Select a measurement for temperature compensation. If not selected, uses the onboard sensor.'),
        # },
        {
            'id': 'cal1_v',
            'type': 'float',
            'default_value': 0.,
            'name': 'Cal data: V1 (internal)',
            'phrase': 'Calibration data: Voltage'
        },
        {
            'id': 'cal1_ph',
            'type': 'float',
            'default_value': 7.,
            'name': 'Cal data: pH1 (internal)',
            'phrase': 'Calibration data: pH'
        },
        {
            'id': 'cal1_t',
            'type': 'float',
            'default_value': 23.,
            'name': 'Cal data: T1 (internal)',
            'phrase': 'Calibration data: Temperature'
        },
        {
            'id': 'cal2_v',
            'type': 'float',
            'default_value': 0.17,
            'name': 'Cal data: V2 (internal)',
            'phrase': 'Calibration data: Voltage'
        },
        {
            'id': 'cal2_ph',
            'type': 'float',
            'default_value': 4.,
            'name': 'Cal data: pH2 (internal)',
            'phrase': 'Calibration data: pH'
        },
        {
            'id': 'cal2_t',
            'type': 'float',
            'default_value': 23.,
            'name': 'Cal data: T2 (internal)',
            'phrase': 'Calibration data: Temperature'
        },
        {
            'id': 'cal3_v',
            'type': 'float',
            'default_value': None,
            'name': 'Cal data: V3 (internal)',
            'phrase': 'Calibration data: Voltage'
        },
        {
            'id': 'cal3_ph',
            'type': 'float',
            'default_value': None,
            'name': 'Cal data: pH3 (internal)',
            'phrase': 'Calibration data: pH'
        },
        {
            'id': 'cal3_t',
            'type': 'float',
            'default_value': None,
            'name': 'Cal data: T3 (internal)',
            'phrase': 'Calibration data: Temperature'
        },
    ],
    'custom_actions_message': """Calibrate: Place your probe in a solution of known pH. Set 
the known pH value in the `Calibration buffer pH` field, and press `Calibrate, slot 1`. Repeat with a second buffer,
and press `Calibrate, slot 2`. Optionally, repeat a third time with `Calibrate, slot 3`. You don't need to change
 the values under `Custom Options`.""",
    'custom_actions': [
        {
            'id': 'calibration_ph',
            'type': 'float',
            'default_value': 7.,
            'name': 'Calibration buffer pH',
            'phrase': 'This is the nominal pH of the calibration buffer, usually labelled on the bottle.'
        },
        {
            'id': 'calibrate_slot_1',
            'type': 'button',
            'name': 'Calibrate, slot 1'
        },
        {
            'id': 'calibrate_slot_2',
            'type': 'button',
            'name': 'Calibrate, slot 2'
        },
        {
            'id': 'calibrate_slot_3',
            'type': 'button',
            'name': 'Calibrate, slot 3'
        },
        # todo: Including this input will raise an error about `cannot convert string to float`
        # todo when attempting calibration.
        # {
        #     'id': 'temperature_comp_meas',
        #     'type': 'select_measurement',
        #     'default_value': '',
        #     'options_select': [
        #         'Input',
        #         'Function',
        #         'Math'
        #     ],
        #     'name': lazy_gettext('Temperature Compensation Measurement'),
        #     'phrase': lazy_gettext('Select a measurement for temperature compensation')
        # },
        # {
        #     'id': 'max_age',
        #     'type': 'integer',
        #     'default_value': 120,
        #     'required': True,
        #     'constraints_pass': constraints_pass_positive_value,
        #     'name': lazy_gettext('Temperature Compensation Max Age'),
        #     'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use for temperature compensation')
        # },

    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors AnyLeaf sensor pH or ORP"""
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        # todo: We've temporarily disabled offboard measurements.
        # self.temperature_comp_meas_device_id = None
        # self.temperature_comp_meas_measurement_id = None
        # self.max_age = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        from adafruit_extended_bus import ExtendedI2C
        from anyleaf import PhSensor, CalPt

        self.sensor = PhSensor(
            ExtendedI2C(self.input_dev.i2c_bus),
            self.input_dev.period,
            address=int(str(self.input_dev.i2c_location), 16)
        )

        # `default_value` above doesn't set the default in the database: custom options will initialize to None.
        if self.get_custom_option("cal1_v"):
            cal1_v = self.get_custom_option("cal1_v")
        else:
            cal1_v = 0.
        if self.get_custom_option("cal1_ph"):
            cal1_ph = self.get_custom_option("cal1_ph")
        else:
            cal1_ph = 7.
        if self.get_custom_option("cal1_t"):
            cal1_t = self.get_custom_option("cal1_t")
        else:
            cal1_t = 23.

        if self.get_custom_option("cal2_v"):
            cal2_v = self.get_custom_option("cal2_v")
        else:
            cal2_v = 0.17
        if self.get_custom_option("cal2_ph"):
            cal2_ph = self.get_custom_option("cal2_ph")
        else:
            cal2_ph = 4.
        if self.get_custom_option("cal2_t"):
            cal2_t = self.get_custom_option("cal2_t")
        else:
            cal2_t = 23.

        if self.get_custom_option("cal3_v"):
            cal3_v = self.get_custom_option("cal3_v")
        else:
            cal3_v = None
        if self.get_custom_option("cal3_ph"):
            cal3_ph = self.get_custom_option("cal3_ph")
        else:
            cal3_ph = None
        if self.get_custom_option("cal3_t"):
            cal3_t = self.get_custom_option("cal3_t")
        else:
            cal3_t = None

        # cal pt 3 may be None to indicate 2-pt calibration.
        if cal3_v and cal3_ph and cal3_t:
            cal_pt_3 = CalPt(
                cal3_v,
                cal3_ph,
                cal3_t,
            )
        else:
            cal_pt_3 = None

        cal_pt_3 = None

        # Load cal data from the database.
        self.sensor.calibrate_all(
            CalPt(
                cal1_v,
                cal1_ph,
                cal1_t,
            ),
            CalPt(
                cal2_v,
                cal2_ph,
                cal2_t,
            ),
            cal_pt_3
        )

    def calibrate(self, cal_slot, args_dict):
        """Calibration helper method"""
        from anyleaf import CalSlot

        if 'calibration_ph' not in args_dict:
            self.logger.error("Cannot conduct calibration without a buffer pH value")
            return
        if not isinstance(args_dict['calibration_ph'], float) and not isinstance(args_dict['calibration_ph'], int):
            self.logger.error("buffer value does not represent a number: '{}', type: {}".format(
                args_dict['calibration_ph'], type(args_dict['calibration_ph'])))
            return

        temp_data = self.get_temp_data()

        # For this session
        v, t = self.sensor.calibrate(cal_slot, args_dict['calibration_ph'], temp_data)

        # For future sessions
        if cal_slot == CalSlot.ONE:
            self.set_custom_option("cal1_v", v)
            self.set_custom_option("cal1_ph", args_dict['calibration_ph'])
            self.set_custom_option("cal1_t", t)
        elif cal_slot == CalSlot.TWO:
            self.set_custom_option("cal2_v", v)
            self.set_custom_option("cal2_ph", args_dict['calibration_ph'])
            self.set_custom_option("cal2_t", t)
        else:
            self.set_custom_option("cal3_v", v)
            self.set_custom_option("cal3_ph", args_dict['calibration_ph'])
            self.set_custom_option("cal3_t", t)

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
        """ Auto-calibrate """

        from anyleaf import CalSlot
        self.calibrate(CalSlot.THREE, args_dict)

    @staticmethod
    def get_temp_data():
        """Get the temperature, from onboard or off."""

        from anyleaf import OnBoard
        # if self.temperature_comp_meas_measurement_id:
        #     last_temp_measurement = self.get_last_measurement(
        #         self.temperature_comp_meas_device_id,
        #         self.temperature_comp_meas_measurement_id,
        #         max_age=self.max_age
        #     )

        #     if last_temp_measurement:
        #         temp_data = OffBoard(last_temp_measurement[1])
        #     else:
        #         temp_data = OnBoard()

        # else:
        temp_data = OnBoard()
        
        return temp_data

    def get_measurement(self):
        """ Gets the measurement """
        self.return_dict = copy.deepcopy(measurements_dict)

        if not self.sensor:
            self.logger.error("Input not set up")
            return

        temp_data = self.get_temp_data()
        self.value_set(0, self.sensor.read(temp_data))

        return self.return_dict
