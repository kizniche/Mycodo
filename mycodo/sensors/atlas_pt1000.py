# coding=utf-8
import logging
from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
from mycodo.utils.system_pi import str_is_float
from .base_sensor import AbstractSensor

logger = logging.getLogger("mycodo.sensors.atlas_pt1000")


class AtlasPT1000Sensor(AbstractSensor):
    """ A sensor support class that monitors the PT1000's temperature """

    def __init__(self, interface, device_loc=None, baud_rate=None,
                 i2c_address=None, i2c_bus=None):
        super(AtlasPT1000Sensor, self).__init__()
        self._temperature = 0.0
        self.interface = interface
        if self.interface == 'UART':
            self.atlas_sensor_uart = AtlasScientificUART(device_loc,
                                                         baudrate=baud_rate)
        elif self.interface == 'I2C':
            self.atlas_sensor_i2c = AtlasScientificI2C(
                i2c_address=i2c_address, i2c_bus=i2c_bus)

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

    def info(self):
        conditions_measured = [
            ("Temperature", "temperature", "float", "0.00",
             self._temperature, self.temperature)
        ]
        return conditions_measured

    @property
    def temperature(self):
        """ CPU temperature in celsius """
        if not self._temperature:  # update if needed
            self.read()
        return self._temperature

    def get_measurement(self):
        """ Gets the Atlas PT1000's temperature in Celsius """
        temp = None

        if self.interface == 'UART':
            if self.atlas_sensor_uart.setup:
                lines = self.atlas_sensor_uart.query('R')
                logger.debug("All Lines: {lines}".format(lines=lines))

                if 'check probe' in lines:
                    logger.error('"check probe" returned from sensor')
                elif str_is_float(lines[0]):
                    temp = float(lines[0])
                    logger.debug('Value[0] is float: {val}'.format(val=temp))
                else:
                    logger.error('Value[0] is not float or "check probe": '
                                 '{val}'.format(val=lines[0]))
            else:
                logger.error('UART device is not set up. '
                             'Check the log for errors.')

        elif self.interface == 'I2C':
            if self.atlas_sensor_i2c.setup:
                temp_status, temp_str = self.atlas_sensor_i2c.query('R')
                if temp_status == 'error':
                    logger.error("Sensor read unsuccessful: {err}".format(
                        err=temp_str))
                elif temp_status == 'success':
                    temp = float(temp_str)
            else:
                logger.error('I2C device is not set up.'
                             'Check the log for errors.')

        return temp

    def read(self):
        """
        Takes a reading from the PT-1000 and updates self._temperature

        :returns: None on success or 1 on error
        """
        try:
            self._temperature = self.get_measurement()
            if self._temperature:
                return  # success - no errors
        except Exception as e:
            logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
