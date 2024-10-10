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
        'measurement': 'electrical_conductivity',
        'unit': 'uS_cm'
    },
    1: {
        'measurement': 'total_dissolved_solids',
        'unit': 'ppm'
    },
    2: {
        'measurement': 'salinity',
        'unit': 'ppt'
    },
    3: {
        'measurement': 'specific_gravity',
        'unit': 'unitless'
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
        'measurements_select',
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
        }
    ],

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """Calibration: a one- or two-point calibration can be performed. It's a good idea to clear the calibration before calibrating. Always perform a dry calibration with the probe in the air (not in any fluid). Then perform either a one- or two-point calibration with calibrated solutions. If performing a one-point calibration, use the Single Point Calibration field and button. If performing a two-point calibration, use the Low and High Point Calibration fields and buttons. Allow a minute or two after submerging your probe in a calibration solution for the measurements to equilibrate before calibrating to that solution. The EZO EC circuit default temperature compensation is set to 25 °C. If the temperature of the calibration solution is +/- 2 °C from 25 °C, consider setting the temperature compensation first. Note that at no point should you change the temperature compensation value during calibration. Therefore, if you have previously enabled temperature compensation, allow at least one measurement to occur (to set the compensation value), then disable the temperature compensation measurement while you calibrate. Status messages will be sent to the Daemon Log, accessible from Config -> Mycodo Logs -> Daemon Log."""
        },
        {
            'id': 'clear_calibrate',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Clear Calibration'
        },
        {
            'id': 'dry_calibrate',
            'type': 'button',
            'wait_for_return': True,
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
            'wait_for_return': True,
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
            'wait_for_return': True,
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
            'wait_for_return': True,
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
    """A sensor support class that monitors the Atlas Scientific sensor ElectricalConductivity."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.interface = None

        self.temperature_comp_meas_device_id = None
        self.temperature_comp_meas_measurement_id = None
        self.max_age = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        self.interface = self.input_dev.interface

        try:
            self.atlas_device = setup_atlas_device(self.input_dev)

            if self.temperature_comp_meas_measurement_id:
                self.atlas_command = AtlasScientificCommand(
                    self.input_dev, sensor=self.atlas_device)

            self.set_sensor_settings()
        except Exception:
            self.logger.exception("Exception while initializing sensor")

        # Throw out first measurement of Atlas Scientific sensor, as it may be prone to error
        self.get_measurement()

    def set_sensor_settings(self):
        if self.is_enabled(0):
            self.atlas_device.query('O,EC,1')
        else:
            self.atlas_device.query('O,EC,0')

        if self.is_enabled(1):
            self.atlas_device.query('O,TDS,1')
        else:
            self.atlas_device.query('O,TDS,0')

        if self.is_enabled(2):
            self.atlas_device.query('O,S,1')
        else:
            self.atlas_device.query('O,S,0')

        if self.is_enabled(3):
            self.atlas_device.query('O,SG,1')
        else:
            self.atlas_device.query('O,SG,0')

        self.logger.debug("Measurements enabled: {}".format(
            self.atlas_device.query('O?')))

    def get_measurement(self):
        """Gets the sensor's Electrical Conductivity measurement"""
        if not self.atlas_device.setup:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        return_string = None
        self.return_dict = copy.deepcopy(measurements_dict)

        # Compensate measurement based on a temperature measurement
        if self.temperature_comp_meas_measurement_id and self.atlas_command:
            self.logger.debug("pH sensor set to calibrate temperature")

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

                if last_measurement[1] is None:
                    self.logger.error("Cannot use calibration temperature because it returned None. "
                                      "Fix your temperature measurement and try again.")
                else:
                    if unit != "C":
                        out_value = convert_from_x_to_y_unit(
                            unit, "C", last_measurement[1])
                    else:
                        out_value = last_measurement[1]

                    self.logger.debug(f"Latest temperature used to calibrate: {out_value}")

                    ret_value, ret_msg = self.atlas_command.calibrate('temperature', set_amount=out_value)
                    time.sleep(0.5)

                    self.logger.debug(f"Calibration returned: '{ret_value}', '{ret_msg}'")
                    if logging.getLevelName(self.logger.level) == "DEBUG":
                        self.logger.debug(f"Stored temperature value: {self.atlas_device.query('T,?')}")
            else:
                self.logger.error(f"Calibration measurement not found within the past {self.max_age} seconds")

        # Read device
        atlas_status, atlas_return = self.atlas_device.query('R')
        self.logger.debug("Device Returned: {}: {}".format(atlas_status, atlas_return))

        if atlas_status == 'error':
            self.logger.debug("Sensor read unsuccessful: {err}".format(err=atlas_return))
            return

        # Parse device return data
        if self.interface in ['FTDI', 'UART']:
            # Check for "check probe"
            for each_split in atlas_return:
                if 'check probe' in each_split:
                    self.logger.error('"check probe" returned from sensor')
                    return

            # Find float value in list
            for each_split in atlas_return:
                if "," in each_split or str_is_float(each_split):
                    return_string = each_split
                    break

        elif self.interface == 'I2C':
            return_string = self.atlas_device.build_string(atlas_return)

        if return_string and ',' in return_string:
            # Multiple values returned
            index_place = 0
            return_list = return_string.split(',')
            if (self.is_enabled(0) and
                    len(return_list) > index_place and
                    str_is_float(return_list[index_place])):
                self.value_set(0, float(return_list[index_place]))
                index_place += 1
            if (self.is_enabled(1) and
                    len(return_list) > index_place and
                    str_is_float(return_list[index_place])):
                self.value_set(1, float(return_list[index_place]))
                index_place += 1
            if (self.is_enabled(2) and
                    len(return_list) > index_place and
                    str_is_float(return_list[index_place])):
                self.value_set(2, float(return_list[index_place]))
                index_place += 1
            if (self.is_enabled(3) and
                    len(return_list) > index_place and
                    str_is_float(return_list[index_place])):
                self.value_set(3, float(return_list[index_place]))
        elif str_is_float(return_string):
            # Single value returned
            if self.is_enabled(0):
                self.value_set(0, float(return_string))
            elif self.is_enabled(1):
                self.value_set(1, float(return_string))
            elif self.is_enabled(2):
                self.value_set(2, float(return_string))
            elif self.is_enabled(3):
                self.value_set(3, float(return_string))

        return self.return_dict

    def calibrate(self, level, ec):
        try:
            if level == "clear":
                write_cmd = "Cal,clear"
            elif level == "dry":
                write_cmd = "Cal,dry"
            elif level == "single":
                write_cmd = "Cal,{}".format(ec)
            else:
                write_cmd = "Cal,{},{}".format(level, ec)

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
            self.logger.info("I2C Change command: {}".format(write_cmd))
            self.logger.info("Command returned: {}".format(self.atlas_device.query(write_cmd)))
            self.atlas_device = None
        except:
            self.logger.exception("Exception changing I2C address")
