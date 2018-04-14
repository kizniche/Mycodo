# coding=utf-8
import logging

from mycodo.utils.system_pi import str_is_float
from .base_input import AbstractInput


class AtlasElectricalConductivitySensor(AbstractInput):
    """A sensor support class that monitors the Atlas Scientific sensor ElectricalConductivity"""

    def __init__(self, input_dev, testing=False):
        super(AtlasElectricalConductivitySensor, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.atlas_ec")
        self._electrical_conductivity = None
        self.atlas_sensor_uart = None
        self.atlas_sensor_i2c = None

        if not testing:
            self.logger = logging.getLogger(
                "mycodo.inputs.atlas_ec_{id}".format(id=input_dev.id))
            self.interface = input_dev.interface
            self.device_loc = input_dev.device_loc
            self.i2c_address = int(str(input_dev.location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.input_dev = input_dev
            try:
                self.initialize_sensor()
            except Exception:
                self.logger.exception("Exception while initializing sensor")

    def __repr__(self):
        """ Representation of object """
        return "<{cls}(electrical_conductivity={ec})>".format(
            cls=type(self).__name__,
            ec="{0:.2f}".format(self._electrical_conductivity))

    def __str__(self):
        """ Return Electrical Conductivity information """
        return "Electrical Conductivity: {ec}".format(
            ec="{0:.2f}".format(self._electrical_conductivity))

    def __iter__(self):  # must return an iterator
        """ Atlas Electrical Conductivity sensor iterates through live Electrical Conductivity readings """
        return self

    def next(self):
        """ Get next Electrical Conductivity reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(electrical_conductivity=float(self._electrical_conductivity))

    @property
    def electrical_conductivity(self):
        """ Electrical Conductivity """
        if self._electrical_conductivity is None:  # update if needed
            self.read()
        return self._electrical_conductivity

    def initialize_sensor(self):
        from mycodo.devices.atlas_scientific_i2c import AtlasScientificI2C
        from mycodo.devices.atlas_scientific_uart import AtlasScientificUART
        if self.interface == 'UART':
            self.logger = logging.getLogger(
                "mycodo.inputs.atlas_electrical_conductivity_{uart}".format(
                    uart=self.device_loc))
            self.atlas_sensor_uart = AtlasScientificUART(self.device_loc)
        elif self.interface == 'I2C':
            self.logger = logging.getLogger(
                "mycodo.inputs.atlas_electrical_conductivity_{bus}_{add}".format(
                    bus=self.i2c_bus, add=self.i2c_address))
            self.atlas_sensor_i2c = AtlasScientificI2C(
                i2c_address=self.i2c_address, i2c_bus=self.i2c_bus)

    def get_measurement(self):
        """ Gets the sensor's Electrical Conductivity measurement via UART/I2C """
        self._electrical_conductivity = None
        electrical_conductivity = None

        # Read sensor via UART
        if self.interface == 'UART':
            if self.atlas_sensor_uart.setup:
                lines = self.atlas_sensor_uart.query('R')
                if lines:
                    self.logger.debug(
                        "All Lines: {lines}".format(lines=lines))

                    # 'check probe' indicates an error reading the sensor
                    if 'check probe' in lines:
                        self.logger.error(
                            '"check probe" returned from sensor')
                    # if a string resembling a float value is returned, this
                    # is out measurement value
                    elif str_is_float(lines[0]):
                        electrical_conductivity = float(lines[0])
                        self.logger.debug(
                            'Value[0] is float: {val}'.format(val=electrical_conductivity))
                    else:
                        # During calibration, the sensor is put into
                        # continuous mode, which causes a return of several
                        # values in one string. If the return value does
                        # not represent a float value, it is likely to be a
                        # string of several values. This parses and returns
                        # the first value.
                        if str_is_float(lines[0].split(b'\r')[0]):
                            electrical_conductivity = lines[0].split(b'\r')[0]
                        # Lastly, this is called if the return value cannot
                        # be determined. Watchthe output in the GUI to see
                        # what it is.
                        else:
                            electrical_conductivity = lines[0]
                            self.logger.error(
                                'Value[0] is not float or "check probe": '
                                '{val}'.format(val=electrical_conductivity))
            else:
                self.logger.error('UART device is not set up.'
                                  'Check the log for errors.')

        # Read sensor via I2C
        elif self.interface == 'I2C':
            if self.atlas_sensor_i2c.setup:
                ec_status, ec_str = self.atlas_sensor_i2c.query('R')
                if ec_status == 'error':
                    self.logger.error(
                        "Sensor read unsuccessful: {err}".format(
                            err=ec_str))
                elif ec_status == 'success':
                    electrical_conductivity = float(ec_str)
            else:
                self.logger.error(
                    'I2C device is not set up. Check the log for errors.')

        return electrical_conductivity

    def read(self):
        """
        Takes a reading from the sensor and updates the self._electrical_conductivity value

        :returns: None on success or 1 on error
        """
        try:
            self._electrical_conductivity = self.get_measurement()
            if self._electrical_conductivity is not None:
                return # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
