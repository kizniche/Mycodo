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

    'custom_actions_message':
        'The I2C address can be changed. Enter a new address in the 0xYY format '
        '(e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate and '
        'change the I2C address option after setting the new address.',

    'custom_actions': [
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

    def set_i2c_address(self, args_dict):
        if 'new_i2c_address' not in args_dict:
            self.logger.error("Cannot set new I2C address without an I2C address")
            return
        try:
            i2c_address = int(str(args_dict['new_i2c_address']), 16)
            write_cmd = "I2C,{}".format(i2c_address)
            self.logger.debug("I2C Change command: {}".format(write_cmd))
            self.atlas_device.write(write_cmd)
        except:
            self.logger.exception("Exception changing I2C address")
