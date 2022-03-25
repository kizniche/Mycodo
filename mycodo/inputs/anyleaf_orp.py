# coding=utf-8
import copy

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput

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
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('apt', 'libjpeg-dev', 'libjpeg-dev'),
        ('apt', 'zlib1g-dev', 'zlib1g-dev'),
        ('pip-pypi', 'PIL', 'Pillow==8.1.2'),
        ('pip-pypi', 'scipy', 'scipy==1.8.0'),
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'anyleaf', 'anyleaf==0.1.9')
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
    'custom_commands_message': """Calibrate: Place your probe in a solution of known ORP. Set 
the known ORP value in the `Calibration ORP` field, and press `Calibrate`. You don't need to change
 the values under `Custom Options`.""",
    'custom_commands': [
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
            'wait_for_return': True,
            'name': lazy_gettext('Calibrate'),
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
    """A sensor support class that monitors AnyLeaf sensor pH or ORP."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        self.cal_v = None
        self.cal_orp = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        from adafruit_extended_bus import ExtendedI2C
        from anyleaf import OrpSensor, CalPtOrp

        self.sensor = OrpSensor(
            ExtendedI2C(self.input_dev.i2c_bus),
            self.input_dev.period,
            address=int(str(self.input_dev.i2c_location), 16))

        # Load cal data from the database
        self.sensor.calibrate_all(CalPtOrp(self.cal_v, self.cal_orp,))

    def calibrate(self, args_dict):
        """calibrate."""
        if 'calibration_orp' not in args_dict:
            self.logger.error("Cannot conduct calibration without a buffer ORP value")
            return
        if not isinstance(args_dict['calibration_orp'], float) and not isinstance(args_dict['calibration_orp'], int):
            self.logger.error("buffer value does not represent a number: '{}', type: {}".format(
                args_dict['calibration_orp'], type(args_dict['calibration_orp'])))
            return

        # For this session
        v = self.sensor.calibrate(args_dict['calibration_orp'])

        # For future sessions
        self.set_custom_option("cal_orp", args_dict['calibration_orp'])
        self.set_custom_option("cal_v", v)

    def clear_calibrate_slots(self, args_dict):
        self.delete_custom_option("cal_v")
        self.delete_custom_option("cal_orp")
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], self.input_dev)

    def get_measurement(self):
        """Gets the measurement."""
        self.return_dict = copy.deepcopy(measurements_dict)

        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.value_set(0, self.sensor.read())

        return self.return_dict
