# coding=utf-8
import logging
import time

from mycodo.mycodo_flask.calibration_routes import AtlasScientificCommand
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.system_pi import str_is_float
from .base_sensor import AbstractSensor

logger = logging.getLogger("mycodo.sensors.atlas_ph")


class AtlaspHSensor(AbstractSensor):
    """A sensor support class that monitors the Atlas Scientific sensor pH"""

    def __init__(self, interface, device_loc=None, baud_rate=None,
                 i2c_address=None, i2c_bus=None, sensor_sel=None,
                 testing=False):
        super(AtlaspHSensor, self).__init__()
        self._ph = None
        self.interface = interface
        self.device_loc = device_loc
        self.baud_rate = baud_rate
        self.i2c_address = i2c_address
        self.i2c_bus = i2c_bus
        self.sensor_sel = sensor_sel
        self.atlas_sensor_uart = None
        self.atlas_sensor_i2c = None

        if not testing:
            self.initialize_sensor()

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

    @property
    def ph(self):
        """ pH (potential hydrogen) in moles/liter """
        if self._ph is None:  # update if needed
            self.read()
        return self._ph

    def initialize_sensor(self):
        from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
        from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
        if self.interface == 'UART':
            self.atlas_sensor_uart = AtlasScientificUART(self.device_loc,
                                                         baudrate=self.baud_rate)
        elif self.interface == 'I2C':
            self.atlas_sensor_i2c = AtlasScientificI2C(
                i2c_address=self.i2c_address, i2c_bus=self.i2c_bus)

    def get_measurement(self):
        """ Gets the sensor's pH measurement via UART/I2C """
        self._ph = None

        try:
            if ',' in self.sensor_sel.calibrate_sensor_measure:
                logger.debug("pH sensor set to calibrate temperature")

                device_id = self.sensor_sel.calibrate_sensor_measure.split(',')[0]
                measurement = self.sensor_sel.calibrate_sensor_measure.split(',')[1]
                last_measurement = read_last_influxdb(
                    device_id, measurement, duration_sec=300)
                if last_measurement:
                    logger.debug("Latest temperature used to calibrate: {temp}".format(
                        temp=last_measurement[1]))

                    atlas_command = AtlasScientificCommand(self.sensor_sel)
                    ret_value, ret_msg = atlas_command.calibrate(
                        'temperature', temperature=last_measurement[1])
                    time.sleep(0.5)

                    logger.debug("Calibration returned: {val}, {msg}".format(
                        val=ret_value, msg=ret_msg))

            ph = None
            if self.interface == 'UART':
                if self.atlas_sensor_uart.setup:
                    lines = self.atlas_sensor_uart.query('R')
                    if lines:
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
            elif self.interface == 'I2C':
                if self.atlas_sensor_i2c.setup:
                    ph_status, ph_str = self.atlas_sensor_i2c.query('R')
                    if ph_status == 'error':
                        logger.error("Sensor read unsuccessful: {err}".format(
                            err=ph_str))
                    elif ph_status == 'success':
                        ph = float(ph_str)
                else:
                    logger.error('I2C device is not set up.'
                                 'Check the log for errors.')

            return ph
        except:
            logger.exception(1)

    def read(self):
        """
        Takes a reading from the sensor and updates the self._ph value

        :returns: None on success or 1 on error
        """
        try:
            self._ph = self.get_measurement()
            if self._ph is not None:
                return # success - no errors
        except Exception as e:
            logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
