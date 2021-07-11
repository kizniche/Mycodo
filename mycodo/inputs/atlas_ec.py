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
        'measurement': 'electrical_conductivity',
        'unit': 'uS_cm'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_EC',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Atlas EC',
    'input_library': 'pylibftdi/fcntl/io/serial',
    'measurements_name': 'Electrical Conductivity',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.atlas-scientific.com/conductivity/',
    'url_datasheet': 'https://www.atlas-scientific.com/files/EC_EZO_Datasheet.pdf',

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
    'i2c_location': ['0x64'],
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
            'default_value': """Calibration: a one- or two-point calibration can be performed. It's a good idea to clear the calibration before calibrating. Always perform a dry calibration with the probe in the air (not in any fluid). Then perform either a one- or two-point calibration with calibrated solutions. If performing a one-point calibration, use the Single Point Calibration field and button. If performing a two-point calibration, use the Low and High Point Calibration fields and buttons. Allow a minute or two after submerging your probe in a calibration solution for the measurements to equilibrate before calibrating to that solution. The EZO EC circuit default temperature compensation is set to 25 °C. If the temperature of the calibration solution is +/- 2 °C from 25 °C, consider setting the temperature compensation first. Note that at no point should you change the temperature compensation value during calibration. Therefore, if you have previously enabled temperature compensation, allow at least one measurement to occur (to set the compensation value), then disable the temperature compensation measurement while you calibrate."""
        },
        {
            'id': 'clear_calibrate',
            'type': 'button',
            'name': 'Clear Calibration'
        },
        {
            'id': 'dry_calibrate',
            'type': 'button',
            'name': 'Calibrate Dry'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'single_point_ec',
            'type': 'integer',
            'default_value': 84,
            'name': 'Single Point EC (µS)',
            'phrase': 'The EC (µS) of the single point calibration solution'
        },
        {
            'id': 'single_calibrate',
            'type': 'button',
            'name': 'Calibrate Single Point'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'low_point_ec',
            'type': 'integer',
            'default_value': 12880,
            'name': 'Low Point EC (µS)',
            'phrase': 'The EC (µS) of the low point calibration solution'
        },
        {
            'id': 'low_calibrate',
            'type': 'button',
            'name': 'Calibrate Low Point'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'high_point_ec',
            'type': 'integer',
            'default_value': 80000,
            'name': 'High Point EC (µS)',
            'phrase': 'The EC (µS) of the high point calibration solution'
        },
        {
            'id': 'high_calibrate',
            'type': 'button',
            'name': 'Calibrate High Point'
        },
        {
            'type': 'message',
            'default_value': """The I2C address can be changed. Enter a new address in the 0xYY format (e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and change the I2C address option after setting the new address."""
        },
        {
            'id': 'new_i2c_address',
            'type': 'text',
            'default_value': '0x64',
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
    """A sensor support class that monitors the Atlas Scientific sensor ElectricalConductivity"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.interface = None

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
                self.atlas_command = AtlasScientificCommand(self.input_dev, sensor=self.atlas_device)
        except Exception:
            self.logger.exception("Exception while initializing sensor")

        # Throw out first measurement of Atlas Scientific sensor, as it may be prone to error
        self.get_measurement()

    def get_measurement(self):
        """ Gets the sensor's Electrical Conductivity measurement """
        if not self.atlas_device.setup:
            self.logger.error("Input not set up")
            return

        electrical_conductivity = None
        self.return_dict = copy.deepcopy(measurements_dict)

        # Compensate measurement based on a temperature measurement
        if self.temperature_comp_meas_measurement_id and self.atlas_command:
            self.logger.debug("pH sensor set to calibrate temperature")

            last_measurement = self.get_last_measurement(
                self.temperature_comp_meas_device_id,
                self.temperature_comp_meas_measurement_id,
                max_age=self.max_age)

            if last_measurement:
                self.logger.debug("Latest temperature used to calibrate: {temp}".format(temp=last_measurement[1]))

                ret_value, ret_msg = self.atlas_command.calibrate('temperature', set_amount=last_measurement[1])
                time.sleep(0.5)

                self.logger.debug("Calibration returned: {val}, {msg}".format(val=ret_value, msg=ret_msg))
            else:
                self.logger.error(
                    "Calibration measurement not found within the past "
                    "{} seconds".format(self.max_age))

        # Read sensor via FTDI or UART
        if self.interface in ['FTDI', 'UART']:
            ec_status, ec_list = self.atlas_device.query('R')
            if ec_list:
                self.logger.debug("Returned list: {lines}".format(lines=ec_list))

                # Find float value in list
                float_value = None
                for each_split in ec_list:
                    if str_is_float(each_split):
                        float_value = each_split
                        break

                # 'check probe' indicates an error reading the sensor
                if 'check probe' in ec_list:
                    self.logger.error('"check probe" returned from sensor')
                # if a string resembling a float value is returned, this
                # is our measurement value
                elif str_is_float(float_value):
                    electrical_conductivity = float(float_value)
                    self.logger.debug('Found float value: {val}'.format(val=electrical_conductivity))
                else:
                    self.logger.error('Value or "check probe" not found in list: {val}'.format(val=ec_list))

        # Read sensor via I2C
        elif self.interface == 'I2C':
            ec_status, ec_str = self.atlas_device.query('R')
            if ec_status == 'error':
                self.logger.error("Sensor read unsuccessful: {err}".format(err=ec_str))
            elif ec_status == 'success':
                electrical_conductivity = float(ec_str)

        self.value_set(0, electrical_conductivity)

        return self.return_dict

    def calibrate(self, level, ec):
        try:
            if level == "clear":
                write_cmd = "Cal,clear"
            elif level == "dry":
                write_cmd = "Cal,dry"
            elif level == "single":
                write_cmd = "Cal,{}".format(level, ec)
            else:
                write_cmd = "Cal,{},{}".format(level, ec)
            self.logger.debug("Calibration command: {}".format(write_cmd))
            ret_val = self.atlas_device.write(write_cmd)
            self.logger.info("Command returned: {}".format(ret_val))
            # Verify calibration saved
            write_cmd = "Cal,?"
            self.logger.info("Device Calibrated?: {}".format(
                self.atlas_device.write(write_cmd)))
        except:
            self.logger.exception("Exception calibrating")

    def clear_calibrate(self, args_dict):
        self.calibrate('clear', None)

    def dry_calibrate(self, args_dict):
        self.calibrate('dry', None)

    def single_calibrate(self, args_dict):
        if 'single_point_ec' not in args_dict:
            self.logger.error("Cannot calibrate without calibration solution EC")
            return
        self.calibrate('single', args_dict['single_point_ec'])

    def low_calibrate(self, args_dict):
        if 'low_point_ec' not in args_dict:
            self.logger.error("Cannot calibrate without calibration solution EC")
            return
        self.calibrate('low', args_dict['low_point_ec'])

    def high_calibrate(self, args_dict):
        if 'high_point_ec' not in args_dict:
            self.logger.error("Cannot calibrate without calibration solution EC")
            return
        self.calibrate('high', args_dict['high_point_ec'])

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
            self.atlas_device = None
        except:
            self.logger.exception("Exception changing I2C address")
