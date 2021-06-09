# coding=utf-8
import copy

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.constraints_pass import constraints_pass_positive_value

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
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'libjpeg-dev', 'libjpeg-dev'),
        ('apt', 'zlib1g-dev', 'zlib1g-dev'),
        ('pip-pypi', 'PIL', 'Pillow==8.1.2'),
        ('apt', 'python3-scipy', 'python3-scipy'),
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.1'),
        ('pip-pypi', 'anyleaf', 'anyleaf==0.1.8.1')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x48', '0x49'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'temperature_comp_meas',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function',
                'Math'
            ],
            'name': "{}: {}".format(lazy_gettext('Temperature Compensation'), lazy_gettext('Measurement')),
            'phrase': lazy_gettext('Select a measurement for temperature compensation')
        },
        {
            'id': 'max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{}: {}".format(lazy_gettext('Temperature Compensation'), lazy_gettext('Max Age')),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use')
        },
        {
            'id': 'cal1_v',
            'type': 'float',
            'default_value': 0,
            'name': 'Cal data: V1 (internal)',
            'phrase': 'Calibration data: Voltage'
        },
        {
            'id': 'cal1_ph',
            'type': 'float',
            'default_value': 7.0,
            'name': 'Cal data: pH1 (internal)',
            'phrase': 'Calibration data: pH'
        },
        {
            'id': 'cal1_t',
            'type': 'float',
            'default_value': 23.0,
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
            'default_value': 4.0,
            'name': 'Cal data: pH2 (internal)',
            'phrase': 'Calibration data: pH'
        },
        {
            'id': 'cal2_t',
            'type': 'float',
            'default_value': 23.0,
            'name': 'Cal data: T2 (internal)',
            'phrase': 'Calibration data: Temperature'
        },
        {
            'id': 'cal3_v',
            'type': 'float',
            'default_value': None,
            'required': False,
            'name': 'Cal data: V3 (internal)',
            'phrase': 'Calibration data: Voltage'
        },
        {
            'id': 'cal3_ph',
            'type': 'float',
            'default_value': None,
            'required': False,
            'name': 'Cal data: pH3 (internal)',
            'phrase': 'Calibration data: pH'
        },
        {
            'id': 'cal3_t',
            'type': 'float',
            'default_value': None,
            'required': False,
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
            'default_value': 7.0,
            'name': 'Calibration buffer pH',
            'phrase': 'This is the nominal pH of the calibration buffer, usually labelled on the bottle.'
        },
        {
            'id': 'calibrate_slot_1',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Calibrate, slot 1'
        },
        {
            'id': 'calibrate_slot_2',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Calibrate, slot 2'
        },
        {
            'id': 'calibrate_slot_3',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Calibrate, slot 3'
        },
        {
            'id': 'clear_calibrate_slots',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Clear Calibration Slots'
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors AnyLeaf sensor pH or ORP"""
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        self.cal1_v = None
        self.cal1_ph = None
        self.cal1_t = None
        self.cal2_v = None
        self.cal2_ph = None
        self.cal2_t = None
        self.cal3_v = None
        self.cal3_ph = None
        self.cal3_t = None

        self.temperature_comp_meas_device_id = None
        self.temperature_comp_meas_measurement_id = None
        self.max_age = None

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

        # cal pt 3 may be None to indicate 2-pt calibration.
        if self.cal3_v and self.cal3_ph and self.cal3_t:
            cal_pt_3 = CalPt(self.cal3_v, self.cal3_ph, self.cal3_t)
        else:
            cal_pt_3 = None

        # Load cal data from the database.
        self.sensor.calibrate_all(
            CalPt(self.cal1_v, self.cal1_ph, self.cal1_t),
            CalPt(self.cal2_v, self.cal2_ph, self.cal2_t),
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

    def clear_calibrate_slots(self, args_dict):
        self.delete_custom_option("cal1_v")
        self.delete_custom_option("cal1_ph")
        self.delete_custom_option("cal1_t")
        self.delete_custom_option("cal2_v")
        self.delete_custom_option("cal2_ph")
        self.delete_custom_option("cal2_t")
        self.delete_custom_option("cal3_v")
        self.delete_custom_option("cal3_ph")
        self.delete_custom_option("cal3_t")
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], self.input_dev)

    def get_temp_data(self):
        """Get the temperature, from onboard or off."""
        from anyleaf import OffBoard
        from anyleaf import OnBoard

        last_temp_measurement = None
        if self.temperature_comp_meas_measurement_id:
            last_temp_measurement = self.get_last_measurement(
                self.temperature_comp_meas_device_id,
                self.temperature_comp_meas_measurement_id,
                max_age=self.max_age)

        if last_temp_measurement:
            return OffBoard(last_temp_measurement[1])
        else:
            return OnBoard()

    def get_measurement(self):
        """ Gets the measurement """
        self.return_dict = copy.deepcopy(measurements_dict)

        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.value_set(0, self.sensor.read(self.get_temp_data()))

        return self.return_dict
