# coding=utf-8
import time

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.calibration import AtlasScientificCommand
from mycodo.utils.system_pi import str_is_float


def constraints_pass_positive_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


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
    'input_name': 'EC',
    'measurements_name': 'Electrical Conductivity',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'period',
        'custom_options',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylibftdi', 'pylibftdi')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x64'],
    'i2c_address_editable': True,
    'ftdi_location': '/dev/ttyUSB0',
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,

    'custom_options': [
        {
            'id': 'temperature_comp_meas',
            'type': 'select_measurement',
            'default_value': '',
            'options_select': [
                'Input',
                'Math'
            ],
            'name': lazy_gettext('Temperature Compensation Measurement'),
            'phrase': lazy_gettext('Select a measurement for temperature compensation')
        },
        {
            'id': 'max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Temperature Compensation Max Age'),
            'phrase': lazy_gettext('The maximum age (seconds) of the measurement to use for temperature compensation')
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific sensor ElectricalConductivity"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self.atlas_sensor_ftdi = None
        self.atlas_sensor_uart = None
        self.atlas_sensor_i2c = None

        # Initialize custom options
        self.temperature_comp_meas_device_id = None
        self.temperature_comp_meas_measurement_id = None
        self.max_age = None
        # Set custom options
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.input_dev = input_dev
            self.interface = input_dev.interface

            if self.temperature_comp_meas_measurement_id:
                self.atlas_command = AtlasScientificCommand(self.input_dev)

            try:
                self.initialize_sensor()
            except Exception:
                self.logger.exception("Exception while initializing sensor")

    def initialize_sensor(self):
        from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
        from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
        from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
        if self.interface == 'FTDI':
            self.ftdi_location = self.input_dev.ftdi_location
            self.atlas_sensor_ftdi = AtlasScientificFTDI(self.ftdi_location)
        elif self.interface == 'UART':
            self.uart_location = self.input_dev.uart_location
            self.atlas_sensor_uart = AtlasScientificUART(self.uart_location)
        elif self.interface == 'I2C':
            self.i2c_address = int(str(self.input_dev.i2c_location), 16)
            self.i2c_bus = self.input_dev.i2c_bus
            self.atlas_sensor_i2c = AtlasScientificI2C(
                i2c_address=self.i2c_address, i2c_bus=self.i2c_bus)

    def get_measurement(self):
        """ Gets the sensor's Electrical Conductivity measurement via UART/I2C """
        electrical_conductivity = None
        self.return_dict = measurements_dict.copy()

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
                    "Calibration measurement not found within the past "
                    "{} seconds".format(self.max_age))

        # Read sensor via FTDI
        if self.interface == 'FTDI':
            if self.atlas_sensor_ftdi.setup:
                lines = self.atlas_sensor_ftdi.query('R')
                if lines:
                    self.logger.debug(
                        "All Lines: {lines}".format(lines=lines))

                    # 'check probe' indicates an error reading the sensor
                    if 'check probe' in lines:
                        self.logger.error(
                            '"check probe" returned from sensor')
                    # if a string resembling a float value is returned, this
                    # is out measurement value
                    elif str_is_float(lines[0]):
                        electrical_conductivity = float(lines[0])
                        self.logger.debug(
                            'Value[0] is float: {val}'.format(val=electrical_conductivity))
                    else:
                        # During calibration, the sensor is put into
                        # continuous mode, which causes a return of several
                        # values in one string. If the return value does
                        # not represent a float value, it is likely to be a
                        # string of several values. This parses and returns
                        # the first value.
                        if str_is_float(lines[0].split(b'\r')[0]):
                            electrical_conductivity = lines[0].split(b'\r')[0]
                        # Lastly, this is called if the return value cannot
                        # be determined. Watchthe output in the GUI to see
                        # what it is.
                        else:
                            electrical_conductivity = lines[0]
                            self.logger.error(
                                'Value[0] is not float or "check probe": '
                                '{val}'.format(val=electrical_conductivity))
            else:
                self.logger.error('FTDI device is not set up.'
                                  'Check the log for errors.')

        # Read sensor via UART
        elif self.interface == 'UART':
            if self.atlas_sensor_uart.setup:
                lines = self.atlas_sensor_uart.query('R')
                if lines:
                    self.logger.debug(
                        "All Lines: {lines}".format(lines=lines))

                    # 'check probe' indicates an error reading the sensor
                    if 'check probe' in lines:
                        self.logger.error(
                            '"check probe" returned from sensor')
                    # if a string resembling a float value is returned, this
                    # is out measurement value
                    elif str_is_float(lines[0]):
                        electrical_conductivity = float(lines[0])
                        self.logger.debug(
                            'Value[0] is float: {val}'.format(val=electrical_conductivity))
                    else:
                        # During calibration, the sensor is put into
                        # continuous mode, which causes a return of several
                        # values in one string. If the return value does
                        # not represent a float value, it is likely to be a
                        # string of several values. This parses and returns
                        # the first value.
                        if str_is_float(lines[0].split(b'\r')[0]):
                            electrical_conductivity = lines[0].split(b'\r')[0]
                        # Lastly, this is called if the return value cannot
                        # be determined. Watchthe output in the GUI to see
                        # what it is.
                        else:
                            electrical_conductivity = lines[0]
                            self.logger.error(
                                'Value[0] is not float or "check probe": '
                                '{val}'.format(val=electrical_conductivity))
            else:
                self.logger.error('UART device is not set up.'
                                  'Check the log for errors.')

        # Read sensor via I2C
        elif self.interface == 'I2C':
            if self.atlas_sensor_i2c.setup:
                ec_status, ec_str = self.atlas_sensor_i2c.query('R')
                if ec_status == 'error':
                    self.logger.error(
                        "Sensor read unsuccessful: {err}".format(
                            err=ec_str))
                elif ec_status == 'success':
                    electrical_conductivity = float(ec_str)
            else:
                self.logger.error(
                    'I2C device is not set up. Check the log for errors.')

        self.value_set(0, electrical_conductivity)

        return self.return_dict
