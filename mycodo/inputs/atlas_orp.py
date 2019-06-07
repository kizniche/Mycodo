# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
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
        'measurement': 'oxidation_reduction_potential',
        'unit': 'mV'
    }
}


# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_ORP',
    'input_manufacturer': 'Atlas',
    'input_name': 'Atlas ORP',
    'measurements_name': 'Oxidation Reduction Potential',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'uart_baud_rate',
        'period',
        'single_input_math',
        'custom_options',
        'pre_output',
        'log_level_debug'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'filelock', 'filelock'),
        ('pip-pypi', 'pylibftdi', 'pylibftdi')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x66'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',
    'uart_baud_rate': 9600,

    'custom_options': [
        {
            'id': 'max_age',
            'type': 'integer',
            'default_value': 120,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Calibration Max Age'),
            'phrase': lazy_gettext('The Max Age (seconds) of the Input/Math to use for calibration')
        }
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific sensor ORP"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self.atlas_sensor_ftdi = None
        self.atlas_sensor_uart = None
        self.atlas_sensor_i2c = None
        self.ftdi_location = None
        self.uart_location = None
        self.i2c_address = None
        self.i2c_bus = None

        if not testing:
            self.interface = input_dev.interface
            self.calibrate_sensor_measure = input_dev.calibrate_sensor_measure
            self.max_age = None

            if input_dev.custom_options:
                for each_option in input_dev.custom_options.split(';'):
                    option = each_option.split(',')[0]
                    value = each_option.split(',')[1]
                    if option == 'max_age':
                        self.max_age = int(value)

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
        """ Gets the sensor's ORP measurement via UART/I2C """
        orp = None
        self.return_dict = measurements_dict.copy()

        # Read sensor via UART
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
                        orp = float(lines[0])
                        self.logger.debug(
                            'Value[0] is float: {val}'.format(val=orp))
                    else:
                        # During calibration, the sensor is put into
                        # continuous mode, which causes a return of several
                        # values in one string. If the return value does
                        # not represent a float value, it is likely to be a
                        # string of several values. This parses and returns
                        # the first value.
                        if str_is_float(lines[0].split(b'\r')[0]):
                            orp = lines[0].split(b'\r')[0]
                        # Lastly, this is called if the return value cannot
                        # be determined. Watchthe output in the GUI to see
                        # what it is.
                        else:
                            orp = lines[0]
                            self.logger.error(
                                'Value[0] is not float or "check probe": '
                                '{val}'.format(val=orp))
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
                        orp = float(lines[0])
                        self.logger.debug(
                            'Value[0] is float: {val}'.format(val=orp))
                    else:
                        # During calibration, the sensor is put into
                        # continuous mode, which causes a return of several
                        # values in one string. If the return value does
                        # not represent a float value, it is likely to be a
                        # string of several values. This parses and returns
                        # the first value.
                        if str_is_float(lines[0].split(b'\r')[0]):
                            orp = lines[0].split(b'\r')[0]
                        # Lastly, this is called if the return value cannot
                        # be determined. Watchthe output in the GUI to see
                        # what it is.
                        else:
                            orp = lines[0]
                            self.logger.error(
                                'Value[0] is not float or "check probe": '
                                '{val}'.format(val=orp))
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
                    orp = float(ec_str)
            else:
                self.logger.error(
                    'I2C device is not set up. Check the log for errors.')

        self.value_set(0, orp)

        return self.return_dict
