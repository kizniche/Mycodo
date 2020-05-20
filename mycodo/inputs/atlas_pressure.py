# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements_dict = {
    0: {
        'measurement': 'pressure',
        'unit': 'psi'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_EZO_PRESS',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'Pressure',
    'input_library': 'EZO',
    'measurements_name': 'Pressure',
    'measurements_dict': measurements_dict,

    'options_enabled': [
        'ftdi_location',
        'i2c_location',
        'uart_location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'pylibftdi', 'pylibftdi')
    ],

    'interfaces': ['I2C', 'UART', 'FTDI'],
    'i2c_location': ['0x6a'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0',

    'custom_options': [
        {
            'id': 'led',
            'type': 'select',
            'default_value': 'on',
            'options_select': [
                ('on', 'Always On'),
                ('off', 'Always Off'),
                ('measure', 'Only On During Measure')
            ],
            'name': lazy_gettext('LED Mode'),
            'phrase': lazy_gettext('When to turn the LED on')
        }
    ]
}


class InputModule(AbstractInput):
    """ A sensor support class that acquires measurements from the sensor """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.atlas_sensor = None
        self.led = None

        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.input_dev = input_dev
            self.interface = input_dev.interface

            try:
                self.initialize_sensor()
            except Exception:
                self.logger.exception("Exception while initializing sensor")

            if self.atlas_sensor:
                if self.led == 'on':
                    self.atlas_sensor.query('L,1')
                elif self.led == 'off':
                    self.atlas_sensor.query('L,0')

    def initialize_sensor(self):
        if self.interface == 'FTDI':
            from mycodo.devices.atlas_scientific_ftdi import AtlasScientificFTDI
            self.ftdi_location = self.input_dev.ftdi_location
            self.atlas_sensor = AtlasScientificFTDI(self.ftdi_location)
        elif self.interface == 'UART':
            from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
            self.uart_location = self.input_dev.uart_location
            self.atlas_sensor = AtlasScientificUART(self.uart_location)
        elif self.interface == 'I2C':
            from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
            self.i2c_address = int(str(self.input_dev.i2c_location), 16)
            self.i2c_bus = self.input_dev.i2c_bus
            self.atlas_sensor = AtlasScientificI2C(
                i2c_address=self.i2c_address, i2c_bus=self.i2c_bus)

    def get_measurement(self):
        """ Gets the Atlas Scientific pressure sensor measurement """
        pressure = None
        self.return_dict = measurements_dict.copy()

        if self.led == 'measure':
            self.atlas_sensor.query('L,1')

        if self.interface == 'FTDI':
            if self.atlas_sensor.setup:
                lines = self.atlas_sensor.query('R')
                self.logger.debug("All Lines: {lines}".format(lines=lines))

                if 'check probe' in lines:
                    self.logger.error('"check probe" returned from sensor')
                elif isinstance(lines, list):
                    if str_is_float(lines[0]):
                        pressure = float(lines[0])
                        self.logger.debug(
                            'Value[0] is float: {val}'.format(val=pressure))
                elif str_is_float(lines):
                    pressure = float(lines)
                    self.logger.debug(
                        'Value is float: {val}'.format(val=pressure))
                else:
                    self.logger.error(
                        'Unknown value: {val}'.format(val=lines))
            else:
                self.logger.error('FTDI device is not set up. '
                                  'Check the log for errors.')

        elif self.interface == 'UART':
            if self.atlas_sensor.setup:
                lines = self.atlas_sensor.query('R')
                self.logger.debug("All Lines: {lines}".format(lines=lines))

                if 'check probe' in lines:
                    self.logger.error('"check probe" returned from sensor')
                elif str_is_float(lines[0]):
                    pressure = float(lines[0])
                    self.logger.debug(
                        'Value[0] is float: {val}'.format(val=pressure))
                else:
                    self.logger.error(
                        'Value[0] is not float or "check probe": '
                        '{val}'.format(val=lines[0]))
            else:
                self.logger.error('UART device is not set up. '
                                  'Check the log for errors.')

        elif self.interface == 'I2C':
            if self.atlas_sensor.setup:
                pressure_status, pressure_str = self.atlas_sensor.query('R')
                if pressure_status == 'error':
                    self.logger.error(
                        "Sensor read unsuccessful: {err}".format(
                            err=pressure_str))
                elif pressure_status == 'success':
                    pressure = float(pressure_str)
            else:
                self.logger.error('I2C device is not set up.'
                                  'Check the log for errors.')

        if self.led == 'measure':
            self.atlas_sensor.query('L,0')

        self.value_set(0, pressure)

        return self.return_dict
