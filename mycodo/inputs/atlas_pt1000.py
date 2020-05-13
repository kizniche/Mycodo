# coding=utf-8
from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.system_pi import str_is_float

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'ATLAS_PT1000',
    'input_manufacturer': 'Atlas Scientific',
    'input_name': 'PT-1000',
    'measurements_name': 'Temperature',
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
    'i2c_location': ['0x66'],
    'i2c_address_editable': True,
    'uart_location': '/dev/ttyAMA0'
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the PT1000's temperature """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)
        self.atlas_sensor_ftdi = None
        self.atlas_sensor_uart = None
        self.atlas_sensor_i2c = None

        if not testing:
            self.input_dev = input_dev
            self.interface = input_dev.interface

            try:
                self.initialize_sensor()
            except Exception:
                self.logger.exception("Exception while initializing sensor")

            # Throw out first measurement of Atlas Scientific sensor, as it may be prone to error
            self.get_measurement()

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
        """ Gets the Atlas PT1000's temperature in Celsius """
        temp = None
        self.return_dict = measurements_dict.copy()

        if self.interface == 'FTDI':
            if self.atlas_sensor_ftdi.setup:
                lines = self.atlas_sensor_ftdi.query('R')
                self.logger.debug("All Lines: {lines}".format(lines=lines))

                if 'check probe' in lines:
                    self.logger.error('"check probe" returned from sensor')
                elif isinstance(lines, list):
                    if str_is_float(lines[0]):
                        temp = float(lines[0])
                        self.logger.debug(
                            'Value[0] is float: {val}'.format(val=temp))
                elif str_is_float(lines):
                    temp = float(lines)
                    self.logger.debug(
                        'Value is float: {val}'.format(val=temp))
                else:
                    self.logger.error(
                        'Unknown value: {val}'.format(val=lines))
            else:
                self.logger.error('FTDI device is not set up. '
                                  'Check the log for errors.')

        elif self.interface == 'UART':
            if self.atlas_sensor_uart.setup:
                lines = self.atlas_sensor_uart.query('R')
                self.logger.debug("All Lines: {lines}".format(lines=lines))

                if 'check probe' in lines:
                    self.logger.error('"check probe" returned from sensor')
                elif str_is_float(lines[0]):
                    temp = float(lines[0])
                    self.logger.debug(
                        'Value[0] is float: {val}'.format(val=temp))
                else:
                    self.logger.error(
                        'Value[0] is not float or "check probe": '
                        '{val}'.format(val=lines[0]))
            else:
                self.logger.error('UART device is not set up. '
                                  'Check the log for errors.')

        elif self.interface == 'I2C':
            if self.atlas_sensor_i2c.setup:
                temp_status, temp_str = self.atlas_sensor_i2c.query('R')
                if temp_status == 'error':
                    self.logger.error(
                        "Sensor read unsuccessful: {err}".format(
                            err=temp_str))
                elif temp_status == 'success':
                    temp = float(temp_str)
            else:
                self.logger.error('I2C device is not set up.'
                                  'Check the log for errors.')

        if temp == -1023:  # Erroneous measurement
            return

        self.value_set(0, temp)

        return self.return_dict
