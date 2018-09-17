# coding=utf-8
# From https://github.com/ControlEverythingCommunity/SHT25/blob/master/Python/SHT25.py
import logging
import time

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units
from mycodo.inputs.sensorutils import calculate_dewpoint

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SHT2x',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SHT2x',
    'measurements_name': 'Humidity/Temperature',
    'measurements_list': ['dewpoint', 'humidity', 'temperature'],
    'options_enabled': ['period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface', 'i2c_location'],

    'interfaces': ['I2C'],
    'i2c_location': ['0x40'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the SHT2x's humidity and temperature
    and calculates the dew point

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.sht2x")
        self._dew_point = None
        self._humidity = None
        self._temperature = None

        if not testing:
            import smbus
            self.logger = logging.getLogger(
                "mycodo.inputs.sht2x_{id}".format(id=input_dev.id))
            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.convert_to_unit = input_dev.convert_to_unit
            self.sht2x = smbus.SMBus(self.i2c_bus)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(dewpoint={dpt})(humidity={hum})(temperature={temp})>".format(
            cls=type(self).__name__,
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Dew Point: {dpt}, Humidity: {hum}, Temperature: {temp}".format(
            dpt="{0:.2f}".format(self._dew_point),
            hum="{0:.2f}".format(self._humidity),
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ SHT2xSensor iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(dewpoint=float('{0:.2f}'.format(self._dew_point)),
                    humidity=float('{0:.2f}'.format(self._humidity)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def dew_point(self):
        """ SHT2x dew point in Celsius """
        if self._dew_point is None:  # update if needed
            self.read()
        return self._dew_point

    @property
    def humidity(self):
        """ SHT2x relative humidity in percent """
        if self._humidity is None:  # update if needed
            self.read()
        return self._humidity

    @property
    def temperature(self):
        """ SHT2x temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the humidity and temperature """
        self._dew_point = None
        self._humidity = None
        self._temperature = None

        dew_point = None
        humidity = None
        temperature = None

        for _ in range(2):
            try:
                # Send temperature measurement command
                # 0xF3(243) NO HOLD master
                self.sht2x.write_byte(self.i2c_address, 0xF3)
                time.sleep(0.5)
                # Read data back, 2 bytes
                # Temp MSB, Temp LSB
                data0 = self.sht2x.read_byte(self.i2c_address)
                data1 = self.sht2x.read_byte(self.i2c_address)
                temperature = -46.85 + (((data0 * 256 + data1) * 175.72) / 65536.0)
                # Send humidity measurement command
                # 0xF5(245) NO HOLD master
                self.sht2x.write_byte(self.i2c_address, 0xF5)
                time.sleep(0.5)
                # Read data back, 2 bytes
                # Humidity MSB, Humidity LSB
                data0 = self.sht2x.read_byte(self.i2c_address)
                data1 = self.sht2x.read_byte(self.i2c_address)
                humidity = -6 + (((data0 * 256 + data1) * 125.0) / 65536.0)
                dew_point = calculate_dewpoint(temperature, humidity)
                return dew_point, humidity, temperature
            except Exception as e:
                self.logger.exception(
                    "Exception when taking a reading: {err}".format(err=e))
            # Send soft reset and try a second read
            self.sht2x.write_byte(self.i2c_address, 0xFE)
            time.sleep(0.1)

        dew_point = convert_units(
            'dewpoint', 'C', self.convert_to_unit, dew_point)

        temperature = convert_units(
            'temperature', 'C', self.convert_to_unit, temperature)

        humidity = convert_units(
            'humidity', 'percent', self.convert_to_unit,
            humidity)

        return dew_point, humidity, temperature

    def read(self):
        """
        Takes a reading from the SHT2x and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            (self._dew_point,
             self._humidity,
             self._temperature) = self.get_measurement()
            if self._dew_point is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
