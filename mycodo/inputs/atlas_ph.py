# coding=utf-8
import copy
import time

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.atlas_calibration import AtlasScientificCommand
from mycodo.utils.atlas_calibration import setup_atlas_device
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements_dict = {
    0: {
        'measurement': 'ion_concentration',
        'unit': 'pH'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_PH',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Atlas pH',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'Ion Concentration',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.atlas-scientific.com/ph/',
    'url_datasheet': 'https://www.atlas-scientific.com/files/pH_EZO_Datasheet.pdf',

    'message': 'Calibration Measurement is an optional setting that provides a temperature measurement (in Celsius) of the water that the pH is being measured from.',

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
        ('pip-pypi', 'pylibftdi', 'pylibftdi==0.19.0')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x63'],
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
        }
    ],

    'custom_actions': [
        {
            'type': 'message',
            'default_value': """Calibration: a one-, two- or three-point calibration can be performed. The first calibration must be the Mid point. The second must be the Low point. And the third must be the High point. You can perform a one-, two- or three-point calibration, but they must be performed in this order. Allow a minute or two after submerging your probe in a calibration solution for the measurements to equilibrate before calibrating to that solution. The EZO pH circuit default temperature compensation is set to 25 °C. If the temperature of the calibration solution is +/- 2 °C from 25 °C, consider setting the temperature compensation first. Note that if you have a Temperature Compensation Measurement selected from the Options, this will overwrite the manual Temperature Compensation set here, so be sure to disable this option if you would like to specify the temperature to compensate with."""
        },
        {
            'id': 'compensation_temp_c',
            'type': 'float',
            'default_value': 25.0,
            'name': 'Compensation Temperature (°C)',
            'phrase': 'The temperature of the calibration solutions'
        },
        {
            'id': 'compensation_temp_set',
            'type': 'button',
            'name': 'Set Temperature Compensation'
        },
        {
            'id': 'calibrate_clear',
            'type': 'button',
            'name': lazy_gettext('Clear Calibration')
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'mid_point_ph',
            'type': 'float',
            'default_value': 7.0,
            'name': 'Mid Point pH',
            'phrase': 'The pH of the mid point calibration solution'
        },
        {
            'id': 'mid_calibrate',
            'type': 'button',
            'name': 'Calibrate Mid'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'low_point_ph',
            'type': 'float',
            'default_value': 4.0,
            'name': 'Low Point pH',
            'phrase': 'The pH of the low point calibration solution'
        },
        {
            'id': 'low_calibrate',
            'type': 'button',
            'name': 'Calibrate Low'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'high_point_ph',
            'type': 'float',
            'default_value': 10.0,
            'name': 'High Point pH',
            'phrase': 'The pH of the high point calibration solution'
        },
        {
            'id': 'high_calibrate',
            'type': 'button',
            'name': 'Calibrate High'
        },
        {
            'type': 'message',
            'default_value': """The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address."""
        },
        {
            'id': 'new_i2c_address',
            'type': 'text',
            'default_value': '0x63',
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
    """A sensor support class that monitors the Atlas Scientific sensor pH"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.interface = None
        self.atlas_command = None

        self.temperature_comp_meas_device_id = None
        self.temperature_comp_meas_measurement_id = None
        self.max_age = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        self.interface = self.input_dev.interface

        try:
            self.atlas_device = setup_atlas_device(self.input_dev)

            if self.temperature_comp_meas_measurement_id:
                self.atlas_command = AtlasScientificCommand(
                    self.input_dev, sensor=self.atlas_device)
        except Exception:
            self.logger.exception("Exception while initializing sensor")

        # Throw out first measurement of Atlas Scientific sensor, as it may be prone to error
        self.get_measurement()

    def get_measurement(self):
        """ Gets the sensor's pH measurement """
        if not self.atlas_device.setup:
            self.logger.error("Input not set up")
            return

        ph = None
        self.return_dict = copy.deepcopy(measurements_dict)

        # Compensate measurement based on a temperature measurement
        if self.temperature_comp_meas_measurement_id and self.atlas_command:
            self.logger.debug("pH sensor set to calibrate temperature")

            last_measurement = self.get_last_measurement(
                self.temperature_comp_meas_device_id,
                self.temperature_comp_meas_measurement_id,
                max_age=self.max_age)

            if last_measurement:
                self.logger.debug(
                    "Latest temperature used to calibrate: {temp}".format(
                        temp=last_measurement[1]))
                ret_value, ret_msg = self.atlas_command.calibrate(
                    'temperature', set_amount=last_measurement[1])
                time.sleep(0.5)
                self.logger.debug(
                    "Calibration returned: {val}, {msg}".format(
                        val=ret_value, msg=ret_msg))
            else:
                self.logger.error(
                    "Calibration measurement not found within the past {} seconds".format(
                        self.max_age))

        # Read sensor via FTDI or UART
        if self.interface in ['FTDI', 'UART']:
            ph_status, ph_list = self.atlas_device.query('R')
            if ph_list:
                self.logger.debug("Returned list: {lines}".format(lines=ph_list))

            # Find float value in list
            float_value = None
            for each_split in ph_list:
                if str_is_float(each_split):
                    float_value = each_split
                    break

            if 'check probe' in ph_list:
                self.logger.error('"check probe" returned from sensor')
            elif str_is_float(float_value):
                ph = float(float_value)
                self.logger.debug('Found float value: {val}'.format(val=ph))
            else:
                self.logger.error('Value or "check probe" not found in list: {val}'.format(val=ph_list))

        # Read sensor via I2C
        elif self.interface == 'I2C':
            ph_status, ph_str = self.atlas_device.query('R')
            if ph_status == 'error':
                self.logger.error("Sensor read unsuccessful: {err}".format(err=ph_str))
            elif ph_status == 'success':
                if ',' in ph_str and str_is_float(ph_str.split(',')[2]):
                    ph = float(ph_str.split(',')[2])
                elif str_is_float(ph_str):
                    ph = float(ph_str)
                else:
                    self.logger.error("Could not determine pH from returned string: '{}'".format(ph_str))

        self.value_set(0, ph)

        return self.return_dict

    def compensation_temp_set(self, args_dict):
        if 'compensation_temp_c' not in args_dict:
            self.logger.error("Cannot set temperature compensation without temperature")
            return
        try:
            write_cmd = "T,{:.2f}".format(args_dict['compensation_temp_c'])
            self.logger.debug("Compensation command: {}".format(write_cmd))
            ret_val = self.atlas_device.write(write_cmd)
            self.logger.info("Command returned: {}".format(ret_val))
        except:
            self.logger.exception("Exception compensating temperature")

    def calibrate_clear(self, args_dict):
        try:
            write_cmd = "Cal,clear"
            self.logger.debug("Calibration command: {}".format(write_cmd))
            ret_val = self.atlas_device.write(write_cmd)
            self.logger.info("Command returned: {}".format(ret_val))
        except:
            self.logger.exception("Exception calibrating")

    def calibrate(self, level, ph):
        try:
            write_cmd = "Cal,{},{:.2f}".format(level, ph)
            self.logger.debug("Calibration command: {}".format(write_cmd))
            ret_val = self.atlas_device.write(write_cmd)
            self.logger.info("Command returned: {}".format(ret_val))
            # Verify calibration saved
            write_cmd = "Cal,?"
            self.logger.info("Device Calibrated?: {}".format(
                self.atlas_device.write(write_cmd)))
        except:
            self.logger.exception("Exception calibrating")

    def mid_calibrate(self, args_dict):
        if 'mid_point_ph' not in args_dict:
            self.logger.error("Cannot calibrate without calibration solution ph")
            return
        self.calibrate('mid', args_dict['mid_point_ph'])

    def low_calibrate(self, args_dict):
        if 'low_point_ph' not in args_dict:
            self.logger.error("Cannot calibrate without calibration solution ph")
            return
        self.calibrate('low', args_dict['low_point_ph'])

    def high_calibrate(self, args_dict):
        if 'high_point_ph' not in args_dict:
            self.logger.error("Cannot calibrate without calibration solution ph")
            return
        self.calibrate('high', args_dict['high_point_ph'])

    def set_i2c_address(self, args_dict):
        if 'new_i2c_address' not in args_dict:
            self.logger.error("Cannot set new I2C address without an I2C address")
            return
        try:
            i2c_address = int(str(args_dict['new_i2c_address']), 16)
            write_cmd = "I2C,{}".format(i2c_address)
            self.logger.debug("I2C Change command: {}".format(write_cmd))
            ret_val = self.atlas_device.write(write_cmd)
            self.logger.info("Command returned: {}".format(ret_val))
        except:
            self.logger.exception("Exception changing I2C address")
