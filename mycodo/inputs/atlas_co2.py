# coding=utf-8
import copy
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.atlas_calibration import setup_atlas_device
from mycodo.utils.system_pi import is_int
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements_dict = {
    0: {
        'measurement': 'co2',
        'unit': 'ppm'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_CO2',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Atlas CO2 (Carbon Dioxide Gas)',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'CO2',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://atlas-scientific.com/co2/',
    'url_datasheet': 'https://atlas-scientific.com/files/EZO_CO2_Datasheet.pdf',

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
    'i2c_location': ['0x69'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    'ftdi_location': '/dev/ttyUSB0',

    'custom_commands_message':
        'The I2C address can be changed. Enter a new address in the 0xYY format '
        '(e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and '
        'change the I2C address option after setting the new address.',

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """A one- or two-point calibration can be performed. After exposing the probe to a concentration of CO2 between 3,000 and 5,000 ppmv until readings stabilize, press Calibrate (High). You can place the probe in a 0 CO2 environment until readings stabilize, then press Calibrate (Zero). You can also clear the currently-saved calibration by pressing Clear Calibration, returning to the factory-set calibration. Status messages will be sent to the Daemon Log, accessible from Config -> Mycodo Logs -> Daemon Log."""
        },
        {
            'id': 'co2_high',
            'type': 'integer',
            'default_value': 3000,
            'name': 'High Point CO2',
            'phrase': 'The high CO2 calibration point (3000 - 5000 ppmv)'
        },
        {
            'id': 'calibrate_high',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Calibrate (High)'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'calibrate_zero',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Calibrate (Zero)'
        },
        {
            'id': 'calibrate_clear',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Clear Calibration')
        },
        {
            'type': 'message',
            'default_value': """The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address."""
        },
        {
            'id': 'new_i2c_address',
            'type': 'text',
            'default_value': '0x69',
            'name': lazy_gettext('New I2C Address'),
            'phrase': lazy_gettext('The new I2C to set the device to')
        },
        {
            'id': 'set_i2c_address',
            'type': 'button',
            'wait_for_return': True,
            'name': lazy_gettext('Set I2C Address')
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific CO2 sensor."""

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

    def get_measurement(self):
        """Gets the sensor's measurement."""
        if not self.atlas_device.setup:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        co2 = None
        self.return_dict = copy.deepcopy(measurements_dict)

        # Read device
        atlas_status, atlas_return = self.atlas_device.query('R')
        self.logger.debug("Device Returned: {}: {}".format(atlas_status, atlas_return))

        if atlas_status == 'error':
            self.logger.debug("Sensor read unsuccessful: {err}".format(err=atlas_return))
            return

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
                co2 = float(float_value)
                self.logger.debug('Found float value: {val}'.format(val=co2))
            else:
                self.logger.error('Value or "check probe" not found in list: {val}'.format(val=atlas_return))

        elif self.interface == 'I2C':
            value = self.atlas_device.build_string(atlas_return)
            if str_is_float(value):
                co2 = float(value)
            else:
                self.logger.debug("Could not determine co2 from returned value: '{}'".format(atlas_return))
                return

        if co2 and co2 < 100:
            self.logger.debug("CO2 measured less than 100, not storing measurement.")
            return

        self.value_set(0, co2)

        return self.return_dict

    def calibrate(self, write_cmd):
        try:
            self.logger.debug(f"Command to send: {write_cmd}")
            cmd_status, cmd_return = self.atlas_device.query(write_cmd)
            cmd_return = self.atlas_device.build_string(cmd_return)
            self.logger.info(f"Command returned: {cmd_status}:{cmd_return}")
            cal_status, cal_return = self.atlas_device.query("Cal,?")
            cal_return = self.atlas_device.build_string(cal_return)
            self.logger.info(f"Device Calibrated?: {cal_status}:{cal_return}")
            return f"Command: {write_cmd}, Returned: {cmd_status}:{cmd_return}, Calibrated?: {cal_status}:{cal_return}"
        except Exception as err:
            self.logger.exception("Exception calibrating sensor")
            return f"Exception calibrating sensor: {err}"

    def calibrate_high(self, args_dict):
        if 'co2_high' not in args_dict:
            self.logger.error("Cannot calibrate without high point CO2 ppmv")
            return
        return self.calibrate("Cal,{}".format(args_dict['co2_high']))

    def calibrate_zero(self, args_dict):
        return self.calibrate("Cal,0")

    def calibrate_clear(self, args_dict):
        return self.calibrate("Cal,clear")

    def set_i2c_address(self, args_dict):
        if 'new_i2c_address' not in args_dict:
            self.logger.error("Cannot set new I2C address without an I2C address")
            return
        try:
            i2c_address = int(str(args_dict['new_i2c_address']), 16)
            write_cmd = "I2C,{}".format(i2c_address)
            self.logger.info("I2C Change command: {}".format(write_cmd))
            self.logger.info("Command returned: {}".format(self.atlas_device.query(write_cmd)))
            self.atlas_device = None
        except:
            self.logger.exception("Exception changing I2C address")
