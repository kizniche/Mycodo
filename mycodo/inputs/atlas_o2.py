# coding=utf-8
import copy
import logging
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import Conversion
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_from_x_to_y_unit
from mycodo.utils.atlas_calibration import AtlasScientificCommand
from mycodo.utils.atlas_calibration import setup_atlas_device
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.system_pi import get_measurement
from mycodo.utils.system_pi import return_measurement_info
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements_dict = {
    0: {
        'measurement': 'o2',
        'unit': 'ppt'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_O2',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Atlas O2 (Oxygen Gas)',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'O2',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://atlas-scientific.com/probes/oxygen-sensor/',
    'url_datasheet': 'https://files.atlas-scientific.com/EZO_O2_datasheet.pdf',

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
    'i2c_location': ['0x6c'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,
    'ftdi_location': '/dev/ttyUSB0',

    'custom_options': [
        {
            'id': 'temperature_comp_meas',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Function'
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
            'name': "{}: {} ({})".format(lazy_gettext('Temperature Compensation'), lazy_gettext('Max Age'), lazy_gettext('Seconds')),
            'phrase': lazy_gettext('The maximum age of the measurement to use')
        },
        {
            'id': 'temp_comp_c',
            'type': 'float',
            'default_value': 20.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': "{}: {}".format(lazy_gettext('Temperature Compensation'), lazy_gettext('Manual')),
            'phrase': 'If not using a measurement, set the temperature to compensate'
        },
        {
            'id': 'led',
            'type': 'select',
            'default_value': 'on',
            'options_select': [
                ('on', lazy_gettext('Always On')),
                ('off', lazy_gettext('Always Off')),
                ('measure', lazy_gettext('Only On During Measure'))
            ],
            'name': lazy_gettext('LED Mode'),
            'phrase': 'When to turn the LED on'
        }
    ],

    'custom_commands_message':
        'The I2C address can be changed. Enter a new address in the 0xYY format '
        '(e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and '
        'change the I2C address option after setting the new address.',

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """A one- or two-point calibration can be performed. After exposing the probe to a specific concentration of O2 until readings stabilize, press Calibrate (High). You can place the probe in a 0% O2 environment until readings stabilize, then press Calibrate (Zero). You can also clear the currently-saved calibration by pressing Clear Calibration, returning to the factory-set calibration. Status messages will be sent to the Daemon Log, accessible from Config -> Mycodo Logs -> Daemon Log."""
        },
        {
            'id': 'co2_high',
            'type': 'float',
            'default_value': 20.95,
            'name': 'High Point O2',
            'phrase': 'The high O2 calibration point (percent)'
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
            'name': lazy_gettext('Set I2C Address')
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific O2 sensor."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.interface = None
        self.atlas_command = None

        self.temperature_comp_meas_device_id = None
        self.temperature_comp_meas_measurement_id = None
        self.max_age = None
        self.temp_comp_c = None
        self.led = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        self.interface = self.input_dev.interface

        try:
            self.atlas_device = setup_atlas_device(self.input_dev)

            self.atlas_device.query('O,PPT,1')
            self.atlas_device.query('O,%,0')

            if self.temperature_comp_meas_measurement_id:
                self.atlas_command = AtlasScientificCommand(
                    self.input_dev, sensor=self.atlas_device)
            elif self.temp_comp_c is not None:
                self.temp_compensation(self.temp_comp_c)
        except Exception:
            self.logger.exception("Exception while initializing sensor")
            return

        if self.led == 'on':
            self.atlas_device.query('L,1')
        elif self.led == 'off':
            self.atlas_device.query('L,0')

    def get_measurement(self):
        """Gets the sensor's measurement."""
        if not self.atlas_device.setup:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        o2 = None
        self.return_dict = copy.deepcopy(measurements_dict)

        # Compensate measurement based on a temperature measurement
        if self.temperature_comp_meas_measurement_id and self.atlas_command:
            self.logger.debug("O2 sensor set to calibrate temperature")

            last_measurement = self.get_last_measurement(
                self.temperature_comp_meas_device_id,
                self.temperature_comp_meas_measurement_id,
                max_age=self.max_age)

            if last_measurement and len(last_measurement) > 1:
                device_measurement = get_measurement(
                    self.temperature_comp_meas_measurement_id)
                conversion = db_retrieve_table_daemon(
                    Conversion, unique_id=device_measurement.conversion_id)
                _, unit, _ = return_measurement_info(
                    device_measurement, conversion)

                if unit != "C":
                    out_value = convert_from_x_to_y_unit(
                        unit, "C", last_measurement[1])
                else:
                    out_value = last_measurement[1]

                self.logger.debug(
                    f"Latest temperature used to calibrate: {out_value}")

                self.temp_compensation(out_value)

                if logging.getLevelName(self.logger.level) == "DEBUG":
                    self.logger.debug(
                        f"Stored temperature value: {self.atlas_device.query('T,?')}")
            else:
                self.logger.error(
                    f"Calibration measurement not found within the past {self.max_age} seconds")

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
                o2 = float(float_value)
                self.logger.debug('Found float value: {val}'.format(val=o2))
            else:
                self.logger.error('Value or "check probe" not found in list: {val}'.format(val=atlas_return))

        elif self.interface == 'I2C':
            value = self.atlas_device.build_string(atlas_return)
            if str_is_float(value):
                o2 = float(value)
            else:
                self.logger.debug("Could not determine o2 from returned value: '{}'".format(atlas_return))
                return

        self.value_set(0, o2)

        return self.return_dict

    def temp_compensation(self, temperature):
        ret_value, ret_msg = self.atlas_command.calibrate(
            'temperature', set_amount=temperature)
        time.sleep(0.5)

        self.logger.debug(
            f"Calibration returned: '{ret_value}', '{ret_msg}'")
        if logging.getLevelName(self.logger.level) == "DEBUG":
            self.logger.debug(
                f"Stored temperature value: {self.atlas_device.query('T,?')}")

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
            self.logger.error("Cannot calibrate without high point O2 percent")
            return
        self.calibrate("Cal,{}".format(args_dict['co2_high']))

    def calibrate_zero(self, args_dict):
        self.calibrate("Cal,0")

    def calibrate_clear(self, args_dict):
        self.calibrate("Cal,clear")

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
