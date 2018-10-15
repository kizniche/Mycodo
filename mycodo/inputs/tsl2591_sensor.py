# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TSL2591',
    'input_manufacturer': 'TAOS',
    'input_name': 'TSL2591',
    'measurements_name': 'Light',
    'measurements_list': ['light'],
    'options_enabled': ['i2c_location', 'period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-git', 'tsl2591', 'git://github.com/maxlklaxl/python-tsl2591.git#egg=tsl2591')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x29'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the TSL2591's lux """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.tsl2591")
        self._lux = None

        if not testing:
            import tsl2591
            self.logger = logging.getLogger(
                "mycodo.tsl2591_{id}".format(id=input_dev.unique_id.split('-')[0]))
            self.i2c_address = int(str(input_dev.i2c_location), 16)
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
