# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MCP9898',
    'input_manufacturer': 'MICROCHIP',
    'input_name': 'MCP9898',
    'measurements_name': 'Temperature',
    'measurements_list': ['temperature'],
    'options_enabled': ['i2c_location', 'period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit_GPIO'),
        ('pip-git', 'Adafruit_MCP9808', 'git://github.com/adafruit/Adafruit_Python_MCP9808.git#egg=adafruit-mcp9808'),
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x18', '0x19', '0x1a', '0x1b', '0x1c', '0x1d', '0x1e', '0x1f'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the MCP9808's temperature """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.mcp9808")
        self._temperature = None

        if not testing:
            from Adafruit_MCP9808 import MCP9808
            self.logger = logging.getLogger(
                "mycodo.mcp9808_{id}".format(id=input_dev.unique_id.split('-')[0]))
            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus

            self.convert_to_unit = input_dev.convert_to_unit
            self.sensor = MCP9808.MCP9808(
                address=self.i2c_address, busnum=self.i2c_bus)
            self.sensor.begin()

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temp})>".format(
            cls=type(self).__name__, temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return temperature information """
        return "Temperature: {}".format("{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ DS18B20Sensor iterates through live temperature readings """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def temperature(self):
        """ MCP9808 temperature in celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the MCP9808's temperature in Celsius """
        self._temperature = None
        temperature = None

        try:
            temperature = self.sensor.readTempC()
        except:
            self.logger.exception("Inout read failure")

        temperature = convert_units(
            'temperature', 'C', self.convert_to_unit,
            temperature)

        return temperature

    def read(self):
        """
        Takes a reading from the MCP9808 and updates the self._temperature value

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
