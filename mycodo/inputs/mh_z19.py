# coding=utf-8
import logging
import time

import fasteners

from .base_input import AbstractInput
from .sensorutils import is_device


class MHZ19Sensor(AbstractInput):
    """ A sensor support class that monitors the MH-Z19's CO2 concentration """

    def __init__(self, device_loc, baud_rate=9600, testing=False):
        super(MHZ19Sensor, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.mh_z19")
        self._co2 = None
        self.mhz19_lock_file = None

        if not testing:
            import serial
            self.logger = logging.getLogger(
                "mycodo.inputs.mhz19.{dev}".format(dev=device_loc.replace('/', '')))
            # Check if device is valid
            self.serial_device = is_device(device_loc)
            if self.serial_device:
                try:
                    self.ser = serial.Serial(self.serial_device,
                                             baudrate=baud_rate,
                                             timeout=1)
                    self.mhz19_lock_file = "/var/lock/sen-mhz19-{}".format(device_loc.replace('/', ''))
                except serial.SerialException:
                    self.logger.exception('Opening serial')
            else:
                self.logger.error(
                    'Could not open "{dev}". '
                    'Check the device location is correct.'.format(
                        dev=device_loc))

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(co2={co2})>".format(
            cls=type(self).__name__,
            co2="{0:.2f}".format(self._co2))

    def __str__(self):
        """ Return CO2 information """
        return "CO2: {co2}".format(co2="{0:.2f}".format(self._co2))

    def __iter__(self):  # must return an iterator
        """ MH-Z19 iterates through live CO2 readings """
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
        """ Gets the MH-Z19's CO2 concentration in ppmv via UART"""
        self._co2 = None
        co2 = None

        if not self.serial_device:  # Don't measure if device isn't validated
            return None

        # Acquire lock on MHZ19 to ensure more than one read isn't
        # being attempted at once.
        lock = fasteners.InterProcessLock(self.mhz19_lock_file)
        lock_acquired = False

        for _ in range(600):
            lock_acquired = lock.acquire(blocking=False)
            if lock_acquired:
                break
            else:
                time.sleep(0.1)

        if lock_acquired:
            self.ser.flushInput()
            time.sleep(1)
            self.ser.write("\xff\x01\x86\x00\x00\x00\x00\x00\x79".encode())
            time.sleep(.01)
            resp = self.ser.read(9)
            if len(resp) != 0:
                high = resp[2]
                low = resp[3]
                co2 = (high * 256) + low
            lock.release()
        else:
            self.logger.error("Could not acquire MHZ19 lock")

        return co2

    def read(self):
        """
        Takes a reading from the MH-Z19 and updates the self._co2 value

        :returns: None on success or 1 on error
        """
        try:
            self._co2 = self.get_measurement()
            if self._co2 is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.error(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
