# coding=utf-8
import logging

from mycodo.utils.system_pi import str_is_float
from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units

# Input information
INPUT_INFORMATION = {
    'unique_name_input': 'ATLAS_PT1000',
    'input_manufacturer': 'Atlas',
    'common_name_input': 'Atlas PT-1000',
    'common_name_measurements': 'Temperature',
    'unique_name_measurements': ['temperature'],  # List of strings
    'dependencies_pip': [],  # List of strings
    'interfaces': ['I2C', 'UART'],  # List of strings
    'i2c_location': ['0x66'],  # List of strings
    'i2c_address_editable': True,  # Boolean
    'uart_location': '/dev/ttyAMA0',
    'options_enabled': ['i2c_location', 'uart_location', 'period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface']
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the PT1000's temperature """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.atlas_pt1000")
        self._temperature = None
        self.atlas_sensor_uart = None
        self.atlas_sensor_i2c = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.atlas_pt1000_{id}".format(id=input_dev.id))
            self.interface = input_dev.interface
            if self.interface == 'UART':
                self.uart_location = input_dev.uart_location
            elif self.interface == 'I2C':
                self.i2c_address = int(str(input_dev.i2c_location), 16)
                self.i2c_bus = input_dev.i2c_bus
            self.convert_to_unit = input_dev.convert_to_unit
            self.initialize_sensor()

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})>".format(
            cls=type(self).__name__,
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return temperature information """
        return "Temperature: {temp}".format(
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ Atlas_PT1000Sensor iterates through live temperature readings """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def temperature(self):
        """ CPU temperature in celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def initialize_sensor(self):
        from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
        from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
        if self.interface == 'UART':
            self.logger = logging.getLogger(
                "mycodo.inputs.atlas_pt1000_{loc}".format(
                    loc=self.uart_location))
            self.atlas_sensor_uart = AtlasScientificUART(self.uart_location)
        elif self.interface == 'I2C':
            self.logger = logging.getLogger(
                "mycodo.inputs.atlas_pt1000_{bus}_{add}".format(
                    bus=self.i2c_bus, add=self.i2c_address))
            self.atlas_sensor_i2c = AtlasScientificI2C(
                i2c_address=self.i2c_address, i2c_bus=self.i2c_bus)
        else:
            self.logger = logging.getLogger("mycodo.inputs.atlas_pt1000")

    def get_measurement(self):
        """ Gets the Atlas PT1000's temperature in Celsius """
        self._temperature = None
        temp = None

        if self.interface == 'UART':
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

        temp = convert_units(
            'temperature', 'C', self.convert_to_unit, temp)

        return temp

    def read(self):
        """
        Takes a reading from the PT-1000 and updates self._temperature

        :returns: None on success or 1 on error
        """
        try:
            self._temperature = self.get_measurement()
            if self._temperature is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
