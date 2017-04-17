# coding=utf-8
from lockfile import LockFile
import logging
import serial
import time
import RPi.GPIO as GPIO
from .base_sensor import AbstractSensor

logger = logging.getLogger("mycodo.sensors.atlas_ph")
ATLAS_PH_LOCK_FILE = "/var/lock/sensor-k30"


class AtlaspHUARTSensor(AbstractSensor):
    """ A sensor support class that monitors the K30's CO2 concentration """

    def __init__(self):
        super(AtlaspHUARTSensor, self).__init__()
        self._ph = 0
        if GPIO.RPI_INFO['P1_REVISION'] == 3:
            self.serial_device = "/dev/ttyS0"
        else:
            self.serial_device = "/dev/ttyAMA0"
        self.ser = serial.Serial(port=self.serial_device,
                                 baudrate=38400,
                                 parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE,
                                 bytesize=serial.EIGHTBITS)
        self.ser.close()
        self.ser.open()
        self.ser.isOpen()
        self.ser.flushInput()
        time.sleep(1)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(co2={co2})>".format(
            cls=type(self).__name__,
            co2="{0:.2f}".format(self._ph))

    def __str__(self):
        """ Return CO2 information """
        return "CO2: {co2}".format(co2="{0:.2f}".format(self._ph))

    def __iter__(self):  # must return an iterator
        """ K30 iterates through live CO2 readings """
        return self

    def next(self):
        """ Get next CO2 reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(co2=float('{0:.2f}'.format(self._ph)))

    def info(self):
        conditions_measured = [
            ("pH", "pH", "float", "0.00", self._ph, self.ph)
        ]
        return conditions_measured

    @property
    def ph(self):
        """ pH (potential hydrogen) in moles/liter """
        if not self._ph:  # update if needed
            self.read()
        return self._ph

    def get_measurement(self):
        """ Gets the sensor's pH measurement via UART"""
        self.ser.flushOutput()
        self.ser.write('R\r')
        time.sleep(0.3)
        bytes_read = self.ser.inWaiting()
        if bytes_read != 0:
            ph = self.ser.read(bytes_read)
            self.ser.flushInput()
        else:
            ph = None

        if 'check probe' in ph:
            logger.error('"Check Probe" returned from pH sensor.')
            ph = None

        return ph

    def read(self):
        """
        Takes a reading from the K30 and updates the self._ph value

        :returns: None on success or 1 on error
        """
        lock = LockFile(ATLAS_PH_LOCK_FILE)
        try:
            # Acquire lock to ensure more than one read isn't
            # being attempted at once.
            while not lock.i_am_locking():
                try:
                    lock.acquire(timeout=60)  # wait up to 60 seconds before breaking lock
                except Exception as e:
                    logger.error("{cls} 60 second timeout, {lock} lock broken: "
                                 "{err}".format(cls=type(self).__name__,
                                                lock=ATLAS_PH_LOCK_FILE,
                                                err=e))
                    lock.break_lock()
                    lock.acquire()
            self._ph = self.get_measurement()
            lock.release()
            if self._ph is None:
                return 1
            return  # success - no errors
        except Exception as e:
            logger.error("{cls} raised an exception when taking a reading: "
                         "{err}".format(cls=type(self).__name__, err=e))
            lock.release()
            return 1
