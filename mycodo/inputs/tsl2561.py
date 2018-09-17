# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'TSL2561',
    'input_manufacturer': 'TAOS',
    'input_name': 'TSL2561',
    'measurements_name': 'Light',
    'measurements_list': ['light'],
    'options_enabled': ['i2c_location', 'period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'tsl2561','tsl2561')
    ],
    'interfaces': ['I2C'],
    'i2c_location': ['0x39'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the TSL2561's lux """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.tsl2561")
        self._lux = None

        if not testing:
            from tsl2561 import TSL2561
            self.logger = logging.getLogger(
                "mycodo.inputs.tsl2561_{id}".format(id=input_dev.id))
            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.convert_to_unit = input_dev.convert_to_unit
            self.tsl = TSL2561(address=self.i2c_address, busnum=self.i2c_bus)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(lux={lux})>".format(cls=type(self).__name__,
                                           lux="{0:.2f}".format(self._lux))

    def __str__(self):
        """ Return lux information """
        return "Lux: {lux}".format(lux="{0:.2f}".format(self._lux))

    def __iter__(self):  # must return an iterator
        """ TSL2561Sensor iterates through live lux readings """
        return self

    def next(self):
        """ Get next lux reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(lux=float('{0:.2f}'.format(self._lux)))

    @property
    def lux(self):
        """ TSL2561 luminosity in lux """
        if not self._lux:  # update if needed
            self.read()
        return self._lux

    def get_measurement(self):
        """ Gets the TSL2561's lux """
        self._lux = None
        saturated = False
        try:
            lux = convert_units(
                'light', 'lux', self.convert_to_unit,
                self.tsl.lux())
            return lux
        except Exception as err:
            if 'saturated' in repr(err):
                self.logger.error(
                    "Could not obtain measurement: Sensor is saturated. "
                    "Setting integration time to 101 ms and trying again")
                saturated = True
            else:
                self.logger.exception("Error: {}".format(err))

        if saturated:
            from tsl2561.constants import TSL2561_INTEGRATIONTIME_101MS
            self.tsl.set_integration_time(TSL2561_INTEGRATIONTIME_101MS)
            saturated = False
            try:
                lux = convert_units(
                    'light', 'lux', self.convert_to_unit,
                    self.tsl.lux())
                return lux
            except Exception as err:
                if 'saturated' in repr(err):
                    self.logger.error(
                        "Could not obtain measurement: Sensor is saturated. "
                        "Setting integration time to 13 ms and trying again")
                    saturated = True
                else:
                    self.logger.exception("Error: {}".format(err))

        if saturated:
            from tsl2561.constants import TSL2561_INTEGRATIONTIME_13MS
            self.tsl.set_integration_time(TSL2561_INTEGRATIONTIME_13MS)
            try:
                lux = convert_units(
                    'light', 'lux', self.convert_to_unit,
                    self.tsl.lux())
                return lux
            except Exception as err:
                if 'saturated' in repr(err):
                    self.logger.error(
                        "Could not obtain measurement: Sensor is saturated. "
                        "Recording value as 65536.")
                    return 65536.0
                else:
                    self.logger.exception("Error: {}".format(err))

    def read(self):
        """
        Takes a reading from the TSL2561 and updates the self._lux value

        :returns: None on success or 1 on error
        """
        try:
            self._lux = self.get_measurement()
            if self._lux is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
