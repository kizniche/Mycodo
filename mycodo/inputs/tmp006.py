# coding=utf-8
import logging

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import convert_units

# Input information
INPUT_INFORMATION = {
    'unique_name_input': 'TMP006',
    'input_manufacturer': 'Texas Instruments',
    'common_name_input': 'TMP006',
    'common_name_measurements': 'Temperature (Object/Die)',
    'unique_name_measurements': ['temperature_object', 'temperature_die'],  # List of strings
    'dependencies_pip': ['Adafruit_TMP'],  # List of strings
    'interfaces': ['I2C'],  # List of strings
    'i2c_location': ['0x40', '0x41', '0x42', '0x43', '0x44', '0x45', '0x46', '0x47'],  # List of strings
    'i2c_address_editable': False,  # Boolean
    'options_enabled': ['i2c_location', 'period', 'convert_unit', 'pre_output'],
    'options_disabled': ['interface']
}


class InputModule(AbstractInput):
    """ A sensor support class that monitors the TMP006's die and object temperatures """

    def __init__(self, input_dev,  testing=False):
        super(InputModule, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.tmp006")
        self._temperature_die = None
        self._temperature_object = None

        if not testing:
            from Adafruit_TMP import TMP006
            self.logger = logging.getLogger(
                "mycodo.inputs.tmp006_{id}".format(id=input_dev.id))
            self.i2c_address = int(str(input_dev.i2c_location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.convert_to_unit = input_dev.convert_to_unit
            self.sensor = TMP006.TMP006(
                address=self.i2c_address, busnum=self.i2c_bus)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature_die={tdie})(temperature_object={tobj})>".format(
            cls=type(self).__name__,
            tdie="{0:.2f}".format(self._temperature_die),
            tobj="{0:.2f}".format(self._temperature_object))

    def __str__(self):
        """ Return temperature information """
        return "Temperature (Die): {tdie}, Temperature (Object): {tobj}".format(
            tdie="{0:.2f}".format(self._temperature_die),
            tobj="{0:.2f}".format(self._temperature_object))

    def __iter__(self):  # must return an iterator
        """ TMP006Sensor iterates through live temperature readings """
        return self

    def next(self):
        """ Get next temperature reading """
        if self.read():  # raised an error
            raise StopIteration  # required
        return dict(temperature_die=float('{0:.2f}'.format(self._temperature_die)),
                    temperature_object=float('{0:.2f}'.format(self._temperature_object)))

    @property
    def temperature_die(self):
        """ Die temperature in celsius """
        if self._temperature_die is None:  # update if needed
            self.read()
        return self._temperature_die

    @property
    def temperature_object(self):
        """ Object temperature in celsius """
        if self._temperature_object is None:  # update if needed
            self.read()
        return self._temperature_object

    def get_measurement(self):
        """ Gets the TMP006's temperature in Celsius """
        self._temperature_die = None
        self._temperature_object = None

        self.sensor.begin()

        temperature_die = convert_units(
            'temperature_die', 'C', self.convert_to_unit,
            self.sensor.readDieTempC())

        temperature_object = convert_units(
            'temperature_object', 'C', self.convert_to_unit,
            self.sensor.readObjTempC())

        return temperature_die, temperature_object

    def read(self):
        """
        Takes a reading from the TMP006 and updates the self._temperature_die
        and self._temperature_object values

        :returns: None on success or 1 on error
        """
        try:
            self._temperature_die, self._temperature_object = self.get_measurement()
            if self._temperature_die is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
