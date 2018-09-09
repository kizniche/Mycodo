# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units

# Input information
INPUT_INFORMATION = {
    'unique_name_input': 'TSL2591',
    'input_manufacturer': 'TAOS',
    'common_name_input': 'TSL2591',
    'common_name_measurements': 'Light',
    'unique_name_measurements': ['light'],  # List of strings
    'dependencies_pypi': ['tsl2591'],  # List of strings
    'interfaces': ['I2C'],  # List of strings
    'i2c_location': ['0x29'],  # List of strings
    'i2c_address_editable': False,  # Boolean
    'options_enabled': ['i2c_location', 'period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface']
}


class TSL2591Sensor(AbstractInput):
    """ A sensor support class that monitors the TSL2591's lux """

    def __init__(self, input_dev, testing=False):
        super(TSL2591Sensor, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.tsl2591_sensor")
        self._lux = None

        if not testing:
            import tsl2591
            self.logger = logging.getLogger(
                "mycodo.inputs.tsl2591_sensor_{id}".format(id=input_dev.id))
            self.i2c_address = int(str(input_dev.location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.convert_to_unit = input_dev.convert_to_unit
            self.tsl = tsl2591.Tsl2591(i2c_bus=self.i2c_bus,
                                       sensor_address=self.i2c_address)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(lux={lux})>".format(cls=type(self).__name__,
                                           lux="{0:.2f}".format(self._lux))

    def __str__(self):
        """ Return lux information """
        return "Lux: {lux}".format(lux="{0:.2f}".format(self._lux))

    def __iter__(self):  # must return an iterator
        """ TSL2591Sensor iterates through live lux readings """
        return self

    def next(self):
        """ Get next lux reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(lux=float('{0:.2f}'.format(self._lux)))

    @property
    def lux(self):
        """ TSL2591 luminosity in lux """
        if self._lux is None:  # update if needed
            self.read()
        return self._lux

    def get_measurement(self):
        """ Gets the TSL2591's lux """
        full, ir = self.tsl.get_full_luminosity()  # read raw values (full spectrum and ir spectrum)

        # convert raw values to lux (and convert to user-selected unit, if necessary)
        lux = convert_units(
            'light', 'lux', self.convert_to_unit,
            self.tsl.calculate_lux(full, ir))

        return lux

    def read(self):
        """
        Takes a reading from the TSL2591 and updates the self._lux value

        :returns: None on success or 1 on error
        """
        try:
            self._lux = self.get_measurement()
            if self._lux is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.error("{cls} raised an exception when taking a reading: "
                              "{err}".format(cls=type(self).__name__, err=e))
        return 1
