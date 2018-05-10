# coding=utf-8
import logging
import time

from .base_input import AbstractInput
from .sensorutils import is_device


class K30Sensor(AbstractInput):
    """ A sensor support class that monitors the K30's CO2 concentration """

    def __init__(self, input_dev, baud_rate=9600, testing=False):
        super(K30Sensor, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.k30")
        self._co2 = None

        if not testing:
            import serial
            self.logger = logging.getLogger(
                "mycodo.inputs.k30_{id}".format(id=input_dev.id))
            self.device_loc = input_dev.device_loc
            # Check if device is valid
            self.serial_device = is_device(self.device_loc)
            if self.serial_device:
                try:
                    self.ser = serial.Serial(self.serial_device,
                                             baudrate=baud_rate,
                                             timeout=1)
                except serial.SerialException:
                    self.logger.exception('Opening serial')
            else:
                self.logger.error(
                    'Could not open "{dev}". '
                    'Check the device location is correct.'.format(
                        dev=self.device_loc))

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(co2={co2})>".format(
            cls=type(self).__name__, co2="{0:.2f}".format(self._co2))

    def __str__(self):
        """ Return CO2 information """
        return "CO2: {co2}".format(co2="{0:.2f}".format(self._co2))

    def __iter__(self):  # must return an iterator
        """ K30 iterates through live CO2 readings """
        return self

    def next(self):
        """ Get next CO2 reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(co2=float('{0:.2f}'.format(self._co2)))

    @property
    def co2(self):
        """ CO2 concentration in ppmv """
        if self._co2 is None:  # update if needed
            self.read()
        return self._co2

    def get_measurement(self):
        """ Gets the K30's CO2 concentration in ppmv via UART"""
        if not self.serial_device:  # Don't measure if device isn't validated
            return None

        self._co2 = None
        co2= None

        self.ser.flushInput()
        time.sleep(1)
        self.ser.write(bytearray([0xfe, 0x44, 0x00, 0x08, 0x02, 0x9f, 0x25]))
        time.sleep(.01)
        resp = self.ser.read(7)
        if len(resp) != 0:
            high = resp[3]
            low = resp[4]
            co2 = (high * 256) + low

        return co2

    def read(self):
        """
        Takes a reading from the K30 and updates the self._co2 value

        :returns: None on success or 1 on error
        """
        if self.acquiring_measurement:
            self.logger.error("Attempting to acquire a measurement when a"
                              " measurement is already being acquired.")
            return 1
        try:
            self.acquiring_measurement = True
            self._co2 = self.get_measurement()
            if self._co2 is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.error(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        finally:
            self.acquiring_measurement = False
        return 1
