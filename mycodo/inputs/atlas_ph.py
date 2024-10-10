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
from mycodo.utils.system_pi import is_int
from mycodo.utils.system_pi import return_measurement_info
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
        ('pip-pypi', 'pylibftdi', 'pylibftdi==0.20.0')
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
            'default_value': """Calibration: a one-, two- or three-point calibration can be performed. It's a good idea to clear the calibration before calibrating. The first calibration must be the Mid point. The second must be the Low point. And the third must be the High point. You can perform a one-, two- or three-point calibration, but they must be performed in this order. Allow a minute or two after submerging your probe in a calibration solution for the measurements to equilibrate before calibrating to that solution. The EZO pH circuit default temperature compensation is set to 25 °C. If the temperature of the calibration solution is +/- 2 °C from 25 °C, consider setting the temperature compensation first. Note that if you have a Temperature Compensation Measurement selected from the Options, this will overwrite the manual Temperature Compensation set here, so be sure to disable this option if you would like to specify the temperature to compensate with. Status messages will be sent to the Daemon Log, accessible from Config -> Mycodo Logs -> Daemon Log."""
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
            'wait_for_return': True,
            'name': 'Set Temperature Compensation'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'clear_calibrate',
            'type': 'button',
            'wait_for_return': True,
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
            'wait_for_return': True,
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
            'wait_for_return': True,
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
            'wait_for_return': True,
            'name': 'Calibrate High'
        },
        {
            'type': 'message',
            'default_value': """Calibration Export/Import: Export calibration to a series of strings. These can later be imported to restore the calibration. Watch the Daemon Log for the output."""
        },
        {
            'id': 'calibration_export',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Export Calibration'
        },
        {
            'type': 'new_line'
        },
        {
            'id': 'calibration_import_str',
            'type': 'text',
            'default_value': '',
            'name': 'Calibration String',
            'phrase': 'The calibration string to import'
        },
        {
            'id': 'calibration_import',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Import Calibration'
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
    """A sensor support class that monitors the Atlas Scientific sensor pH."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.atlas_device = None
        self.interface = None
        self.atlas_command = None

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
            self.logger.debug(f"Lockfile: {self.atlas_device.lock_file}")

            if self.temperature_comp_meas_measurement_id:
                self.atlas_command = AtlasScientificCommand(
                    self.input_dev, sensor=self.atlas_device)
        except Exception:
            self.logger.exception("Exception while initializing sensor")

        # Throw out first measurement of Atlas Scientific sensor, as it may be prone to error
        self.get_measurement()

    def get_measurement(self):
        """Gets the sensor's pH measurement."""
        if not self.atlas_device.setup:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
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
        self.logger.debug(f"Device Returned: {atlas_status}: {atlas_return}")

        if atlas_status == 'error':
            self.logger.debug(f"Sensor read unsuccessful: {atlas_return}")
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
                ph = float(float_value)
                self.logger.debug(f'Found float value: {ph}')
            else:
                self.logger.error(f'Value or "check probe" not found in list: {atlas_return}')

        elif self.interface == 'I2C':
            return_string = self.atlas_device.build_string(atlas_return)

            if ',' in return_string and str_is_float(return_string.split(',')[2]):
                ph = float(return_string.split(',')[2])
            elif str_is_float(return_string):
                ph = float(return_string)
            else:
                self.logger.error(f"Could not determine pH from returned value: '{return_string}'")

        self.value_set(0, ph)

        return self.return_dict

    def compensation_temp_set(self, args_dict):
        if 'compensation_temp_c' not in args_dict:
            self.logger.error("Cannot set temperature compensation without temperature")
            return

        try:
            write_cmd = f"T,{args_dict['compensation_temp_c']:.2f}"
            self.logger.debug(f"Command to send: {write_cmd}")
            cmd_return = self.atlas_device.build_string(self.atlas_device.query(write_cmd))
            self.logger.info(f"Command returned: {cmd_return}")
            val_return = self.atlas_device.build_string(self.atlas_device.query('T,?'))
            self.logger.info(f"Stored temperature value: {slope_return}")
            return f"Command: {write_cmd}, Returned: {cmd_return}, Stored Temp: {val_return}"
        except Exception as err:
            self.logger.exception("Exception compensating temperature")
            return f"Exception compensating temperature: {err}"

    def calibrate(self, level, ph):
        try:
            if level == "clear":
                write_cmd = "Cal,clear"
            else:
                write_cmd = f"Cal,{level},{ph:.2f}"

            self.logger.debug(f"Command to send: {write_cmd}")
            cmd_status, cmd_return = self.atlas_device.query(write_cmd)
            cmd_return = self.atlas_device.build_string(cmd_return)
            self.logger.info(f"Command returned: {cmd_status}:{cmd_return}")
            cal_status, cal_return = self.atlas_device.query("Cal,?")
            cal_return = self.atlas_device.build_string(cal_return)
            self.logger.info(f"Device Calibrated?: {cal_status}:{cal_return}")
            slope_status, slope_return = self.atlas_device.query('Slope,?')
            slope_return = self.atlas_device.build_string(slope_return)
            self.logger.info(f"Slope: {slope_status}:{slope_return}")
            return f"Command: {write_cmd}, Returned: {cmd_status}:{cmd_return}, Calibrated?: {cal_status}:{cal_return}, Slope: {slope_status}:{slope_return}"
        except Exception as err:
            self.logger.exception("Exception calibrating sensor")
            return f"Exception calibrating sensor: {err}"

    def clear_calibrate(self, args_dict):
        self.calibrate('clear', None)

    def mid_calibrate(self, args_dict):
        if 'mid_point_ph' not in args_dict:
            self.logger.error("Cannot calibrate without calibration solution pH")
            return
        self.calibrate('mid', args_dict['mid_point_ph'])

    def low_calibrate(self, args_dict):
        if 'low_point_ph' not in args_dict:
            self.logger.error("Cannot calibrate without calibration solution pH")
            return
        self.calibrate('low', args_dict['low_point_ph'])

    def high_calibrate(self, args_dict):
        if 'high_point_ph' not in args_dict:
            self.logger.error("Cannot calibrate without calibration solution pH")
            return
        self.calibrate('high', args_dict['high_point_ph'])

    def calibration_export(self, args_dict):
        try:
            atlas_status, atlas_return = self.atlas_device.query("Export,?")
            self.logger.info(f"Command returned: {atlas_return}")
            if atlas_return and ',' in atlas_return:
                list_return = atlas_return.split(',')
                length = None
                bytes = None
                for each_item in list_return:
                    if is_int(each_item):
                        if length is None:
                            length = int(each_item)
                        elif bytes is None:
                            bytes = int(each_item)
                            break
                list_export = []
                for _ in range(length):
                    atlas_status, atlas_return = self.atlas_device.query("Export")
                    if atlas_return:
                        list_export.append(atlas_return)
                atlas_status, atlas_return = self.atlas_device.query("Export")
                if atlas_return != "*DONE":
                    self.logger.error("Did not receive *DONE response indicating export ended")
                self.logger.info(f"pH Calibration export string: {','.join(list_export)}")

            atlas_status, atlas_return = self.atlas_device.query("Slope,?")
            if atlas_status == "success":
                self.logger.info(f"Slope: {atlas_return}")
        except:
            self.logger.exception("Exception exporting calibrating")
        return "Check the Daemon Log to see if the export was successful"

    def calibration_import(self, args_dict):
        if 'calibration_import_str' not in args_dict:
            self.logger.error("Cannot import calibration without calibration string")
            return
        try:
            if "," in args_dict['calibration_import_str']:
                list_strings = args_dict['calibration_import_str'].split(',')
                self.logger.info("Importing calibration string...")

                for each_str in list_strings:
                    try:
                        self.atlas_device.query(f"Import,{each_str}")
                    except:
                        pass
                    time.sleep(1)

                self.logger.info(
                    "Calibration imported. There bay be a Remote I/O Error, but this doesn't mean the "
                    "calibration import failed. Verify it was successful by exporting it. "
                    "Getting calibration slope...")

                atlas_status, atlas_return = self.atlas_device.query("Slope,?")
                if atlas_status == "success":
                    self.logger.info(f"pH Calibration Slope: {atlas_return}")
            else:
                self.logger.error('Calibration string does not contain a comma (",")')
            time.sleep(2)
        except:
            self.logger.exception("Exception importing calibrating")
        return "Check the Daemon Log to see if the import was successful"

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
