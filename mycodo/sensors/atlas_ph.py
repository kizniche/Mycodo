# coding=utf-8
from lockfile import LockFile
import logging
import time
from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
from mycodo.utils.system_pi import str_is_float
from .base_sensor import AbstractSensor

logger = logging.getLogger("mycodo.sensors.atlas_ph")
ATLAS_PH_LOCK_FILE = "/var/lock/sensor-atlas-ph"


class AtlaspHSensor(AbstractSensor):
    """A sensor support class that monitors the Atlas Scientific sensor pH"""

    def __init__(self, interface, device_loc=None, baud_rate=None,
                 i2c_address=None, i2c_bus=None):
        super(AtlaspHSensor, self).__init__()
        self._ph = 0
        self.interface = interface
        if self.interface == 'UART':
            self.atlas_sensor_uart = AtlasScientificUART(
                serial_device=device_loc, baudrate=baud_rate)
        elif self.interface == 'I2C':
            self.atlas_sensor_i2c = AtlasScientificI2C(
                i2c_address=i2c_address, i2c_bus=i2c_bus)

    def __repr__(self):
        """ Representation of object """
        return "<{cls}(ph={ph})>".format(
            cls=type(self).__name__,
            ph="{0:.2f}".format(self._ph))

    def __str__(self):
        """ Return pH information """
        return "pH: {ph}".format(ph="{0:.2f}".format(self._ph))

    def __iter__(self):  # must return an iterator
        """ Atlas pH sensor iterates through live pH readings """
        return self

    def next(self):
        """ Get next pH reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(ph=float(self._ph))

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
        """ Gets the sensor's pH measurement via UART/I2C """
        ph = None
        if self.interface == 'UART':
            if self.atlas_sensor_uart.setup:
                self.atlas_sensor_uart.send_cmd('R')
                time.sleep(1.3)
                lines = self.atlas_sensor_uart.read_lines()
                logger.debug("All Lines: {lines}".format(lines=lines))

                if 'check probe' in lines:
                    logger.error('"check probe" returned from sensor')
                elif str_is_float(lines[0]):
                    ph = float(lines[0])
                    logger.debug('Value[0] is float: {val}'.format(val=ph))
                else:
                    ph = lines[0]
                    logger.error('Value[0] is not float or "check probe": '
                                 '{val}'.format(val=ph))
            else:
                logger.error('UART device is not set up.'
                             'Check the log for errors.')
                ph = None
        elif self.interface == 'I2C':
            if self.atlas_sensor_i2c.setup:
                ph_str = self.atlas_sensor_i2c.query('R')
                if 'Error' in ph_str:
                    raise Exception(
                        "Sensor read unsuccessful: {err}".format(err=ph_str))
                elif 'Command succeeded' in ph_str:
                    ph = float(ph_str[18:24])
            else:
                logger.error('I2C device is not set up.'
                             'Check the log for errors.')
                ph = None
            
        return ph

    def read(self):
        """
        Takes a reading from the sensor and updates the self._ph value

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
