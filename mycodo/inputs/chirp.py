# coding=utf-8
import logging
import time

import smbus

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units

# Input information
INPUT_INFORMATION = {
    'unique_name_input': 'CHIRP',
    'input_manufacturer': 'Catnip Electronics',
    'common_name_input': 'Chirp',
    'common_name_measurements': 'Light/Moisture/Temperature',
    'unique_name_measurements': ['light', 'moisture', 'temperature'],  # List of strings
    'dependencies_pypi': ['smbus'],  # List of strings
    'interfaces': ['I2C'],  # List of strings
    'i2c_location': ['0x40'],  # List of strings
    'i2c_address_editable': True,  # Boolean
    'options_enabled': ['i2c_location', 'period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface']
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the Chirp's moisture, temperature
    and light

    """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.chirp")
        self._lux = None
        self._moisture = None
        self._temperature = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.chirp_{id}".format(id=input_dev.id))
            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.convert_to_unit = input_dev.convert_to_unit
            self.bus = smbus.SMBus(self.i2c_bus)
            self.filter_average('lux', init_max=3)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(lux={lux})(moisture={moist})(temperature={temp})>".format(
            cls=type(self).__name__,
            lux="{0}".format(self._lux),
            moist="{0}".format(self._moisture),
            temp="{0:.2f}".format(self._temperature))

    def __str__(self):
        """ Return measurement information """
        return "Light: {lux}, Moisture: {moist}, Temperature: {temp}".format(
            lux="{0}".format(self._lux),
            moist="{0}".format(self._moisture),
            temp="{0:.2f}".format(self._temperature))

    def __iter__(self):  # must return an iterator
        """ ChirpSensor iterates through live measurement readings """
        return self

    def next(self):
        """ Get next measurement reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(lux=float('{0}'.format(self._lux)),
                    moisture=float('{0}'.format(self._moisture)),
                    temperature=float('{0:.2f}'.format(self._temperature)))

    @property
    def lux(self):
        """ Chirp light measurement """
        if self._lux is None:  # update if needed
            self.read()
        return self._lux

    @property
    def moisture(self):
        """ Chirp moisture measurement """
        if self._moisture is None:  # update if needed
            self.read()
        return self._moisture

    @property
    def temperature(self):
        """ Chirp temperature in Celsius """
        if self._temperature is None:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the light, moisture, and temperature """
        self._lux = None
        self._moisture = None
        self._temperature = None

        lux = self.filter_average('lux', measurement=self.light())
        lux = convert_units(
            'light', 'lux', self.convert_to_unit,
            lux)

        moisture = self.moist()

        temperature = convert_units(
            'temperature', 'C', self.convert_to_unit,
            self.temp() / 10.0)

        return lux, moisture, temperature

    def read(self):
        """
        Takes a reading from the AM2315 and updates the self.dew_point,
        self._humidity, and self._temperature values

        :returns: None on success or 1 on error
        """
        try:
            self._lux, self._moisture, self._temperature = self.get_measurement()
            if self._lux is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1

    def get_reg(self, reg):
        # read 2 bytes from register
        val = self.bus.read_word_data(self.i2c_address, reg)
        # return swapped bytes (they come in wrong order)
        return (val >> 8) + ((val & 0xFF) << 8)

    def reset(self):
        # To reset the sensor, write 6 to the device I2C address
        self.bus.write_byte(self.i2c_address, 6)

    def set_addr(self, new_addr):
        # To change the I2C address of the sensor, write a new address
        # (one byte [1..127]) to register 1; the new address will take effect after reset
        self.bus.write_byte_data(self.i2c_address, 1, new_addr)
        self.reset()
        # self.address = new_addr

    def moist(self):
        # To read soil moisture, read 2 bytes from register 0
        return self.get_reg(0)

    def temp(self):
        # To read temperature, read 2 bytes from register 5
        return self.get_reg(5)

    def light(self):
        # To read light level, start measurement by writing 3 to the
        # device I2C address, wait for 3 seconds, read 2 bytes from register 4
        self.bus.write_byte(self.i2c_address, 3)
        time.sleep(1.5)
        lux = self.get_reg(4)
        if lux == 0:
            return 65535.0
        else:
            return(1 - (lux / 65535.0)) * 65535.0
