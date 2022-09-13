# coding=utf-8
import copy

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.atlas_calibration import setup_atlas_device
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_PT1000',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Atlas PT-1000',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.atlas-scientific.com/temperature/',
    'url_datasheet': 'https://www.atlas-scientific.com/files/EZO_RTD_Datasheet.pdf',

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylibftdi', 'pylibftdi==0.20.0')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x66'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    'ftdi_location': '/dev/ttyUSB0',

    'custom_commands_message':
        'The I2C address can be changed. Enter a new address in the 0xYY format '
        '(e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and '
        'change the I2C address option after setting the new address. '
        'A single point calibration can also be performed for any temperature (°C).',

    'custom_commands': [
        {
            'id': 'new_i2c_address',
            'type': 'text',
            'default_value': '0x66',
            'name': lazy_gettext('New I2C Address'),
            'phrase': lazy_gettext('The new I2C to set the device to')
        },
        {
            'id': 'set_i2c_address',
            'type': 'button',
            'name': lazy_gettext('Set I2C Address')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'calibrate_temp_c',
            'type': 'float',
            'default_value': 100.0,
            'name': "{} (°C)".format(lazy_gettext('Temperature')),
            'phrase': 'Temperature for single point calibration'
        },
        {
            'id': 'calibrate_temp',
            'type': 'button',
            'name': lazy_gettext('Calibrate')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'calibrate_temp_clear',
            'type': 'button',
            'name': 'Clear Calibration'
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the PT1000's temperature."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.interface = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        self.interface = self.input_dev.interface

        try:
            self.atlas_device = setup_atlas_device(self.input_dev)
        except Exception:
            self.logger.exception("Exception while initializing sensor")

        # Throw out first measurement of Atlas Scientific sensor, as it may be prone to error
        self.get_measurement()

    def get_measurement(self):
        """Gets the Atlas PT1000's temperature in Celsius."""
        if not self.atlas_device.setup:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        temp = None
        self.return_dict = copy.deepcopy(measurements_dict)

        # Read device
        atlas_status, atlas_return = self.atlas_device.query('R')
        self.logger.debug("Device Returned: {}: {}".format(atlas_status, atlas_return))

        if atlas_status == 'error':
            self.logger.debug("Sensor read unsuccessful: {err}".format(err=atlas_return))
            return

        # Parse device return data
        if self.interface in ['FTDI', 'UART']:
            # Find float value in list
            float_value = None
            for each_split in atlas_return:
                if str_is_float(each_split):
                    float_value = each_split
                    break

            if 'check probe' in atlas_return:
                self.logger.error('"check probe" returned from sensor')
            elif str_is_float(float_value):
                temp = float(float_value)
                self.logger.debug('Found float value: {val}'.format(val=temp))
            else:
                self.logger.error('Value or "check probe" not found in list: {val}'.format(val=atlas_return))

        elif self.interface == 'I2C':
            value = self.atlas_device.build_string(atlas_return)
            if str_is_float(value):
                temp = float(value)
            else:
                self.logger.debug("Could not determine temp from returned value: '{}'".format(atlas_return))
                return

        if temp == -1023:  # Erroneous measurement
            return

        self.value_set(0, temp)

        return self.return_dict

    def set_i2c_address(self, args_dict):
        if 'new_i2c_address' not in args_dict:
            self.logger.error("Cannot set new I2C address without an I2C address")
            return
        try:
            i2c_address = int(str(args_dict['new_i2c_address']), 16)
            write_cmd = f"I2C,{i2c_address}"
            self.logger.info(f"I2C Change command: {write_cmd}")
            self.logger.info(f"Command returned: {self.atlas_device.query(write_cmd)}")
            self.atlas_device = None
        except:
            self.logger.exception("Exception changing I2C address")

    def calibrate_temp(self, args_dict):
        if 'calibrate_temp_c' not in args_dict:
            self.logger.error("Cannot calibrate without a temperature")
            return
        try:
            write_cmd = f"Cal,{args_dict['calibrate_temp_c']}"
            self.logger.info(f"Calibrate command: {write_cmd}")
            self.logger.info(f"Command returned: {self.atlas_device.query(write_cmd)}")
            cal_status, cal_return = self.atlas_device.query("Cal,?")
            cal_return = self.atlas_device.build_string(cal_return)
            self.logger.info(f"Device Calibrated?: {cal_status}:{cal_return}")
            self.atlas_device = None
        except:
            self.logger.exception("Exception calibrating")

    def calibrate_temp_clear(self, args_dict):
        try:
            write_cmd = f"Cal,clear"
            self.logger.info(f"Calibrate clear command: {write_cmd}")
            self.logger.info(f"Command returned: {self.atlas_device.query(write_cmd)}")
            cal_status, cal_return = self.atlas_device.query("Cal,?")
            cal_return = self.atlas_device.build_string(cal_return)
            self.logger.info(f"Device Calibrated?: {cal_status}:{cal_return}")
            self.atlas_device = None
        except:
            self.logger.exception("Exception clearing calibration")
