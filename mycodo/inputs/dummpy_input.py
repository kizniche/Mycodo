# coding=utf-8
import logging

from flask_babel import lazy_gettext

from .base_input import AbstractInput
from .sensorutils import convert_units


# Input information
INPUT_INFORMATION = {
    'common_name_input': 'Dummy Sensor 001',
    'unique_name_input': 'DUMMY_SEN_001',
    'common_name_measurements': 'Temperature/Humidity',
    'unique_name_measurements': ['temperature', 'humidity'],

    # Measurements (if don't already exist in config_devices_units.py)
    'measurements': {
        'temperature': {
            'name': lazy_gettext('Temperature'),
            'meas': 'temperature',
            'units': ['C', 'F', 'K']
        },
        'humidity': {
            'name': lazy_gettext('Humidity'),
            'meas': 'humidity',
            'units': ['percent', 'decimal']
        }
    },

    # Units (if don't already exist in config_devices_units.py)
    'units': {
        # Temperature
        'C': {
            'name': 'Celsius',
            'unit': '°C'
        },
        'F': {
            'name': 'Fahrenheit',
            'unit': '°F'
        },

        # Humidity
        'decimal': {
            'name': 'Decimal',
            'unit': ''
        },
        'percent': {
            'name': 'Percent',
            'unit': '%'
        }
    },

    # Conversions (if don't already exist in config_devices_units.py)
    'unit_conversions': {
        # Temperature Conversions
        'C_to_F': 'x*(9/5)+32',
        'F_to_C': '(x-32)*5/9',

        # Humidity conversions
        'percent_to_decimal': 'x/100',
        'decimal_to_percent': 'x*100'
    },

    # Python module dependencies
    # This must be a module that is able to be installed with pip via pypi.org
    # Leave the list empty if there are no pip or github dependencies
    'dependencies_pypi': ['w1thermsensor==1.0.5'],
    'dependencies_github': ['git://github.com/adafruit/Adafruit_Python_BME280.git#egg=adafruit-bme280'],

    #
    # The below options are available from the input_dev variable
    # See the example, below: "self.resolution = input_dev.resolution"
    #

    # Interface options: 'I2C' or 'UART'
    'interface': 'I2C',

    # I2C options
    'location': ['0x01', '0x02'],  # I2C address(s). Must be list. Enter more than one if multiple addresses exist.

    # UART options
    'serial_default_baud_rate': 9600,
    'pin_cs': None,
    'pin_miso': None,
    'pin_mosi': None,
    'pin_clock': None,

    # Miscellaneous options available
    'resolution': 12,  # Set 12-bit resolution (for example), accessed from self.resolution
    'resolution_2': None,
    'sensitivity': None,
    'thermocouple_type': None,
}

class DummySensor(AbstractInput):
    """ A dummy sensor support class """

    def __init__(self, input_dev, testing=False):
        super(DummySensor, self).__init__()
        self.logger = logging.getLogger("mycodo.inputs.{name_lower}".format(
            name_lower=INPUT_INFORMATION['unique_name_input'].lower()))

        #
        # Initialize the measurements this input returns
        #
        self._temperature = None
        self._humidity = None

        if not testing:
            #
            # Begin dependent modules loading
            #

            import dependent_module

            #
            # End dependent modules loading
            #

            self.logger = logging.getLogger(
                "mycodo.inputs.{name_lower}_{id}".format(
                    name_lower=INPUT_INFORMATION['unique_name_input'].lower(),
                    id=input_dev.id))
            self.i2c_address = int(str(input_dev.location), 16)
            self.i2c_bus = input_dev.i2c_bus
            self.resolution = input_dev.resolution
            self.convert_to_unit = input_dev.convert_to_unit

            #
            # Initialize the sensor class
            #
            self.sensor = dependent_module.MY_SENSOR_CLASS(
                i2c_address=self.i2c_address,
                i2c_bus=self.i2c_bus,
                resolution=self.resolution)

    def __repr__(self):
        """  Representation of object """
        return "<{cls}(temperature={temperature}(humidity={humidity}))>".format(
            cls=type(self).__name__,
            temperature="{0:.2f}".format(self._temperature),
            humidity="{0:.2f}".format(self._humidity))

    def __str__(self):
        """ Return measurement information """
        return "Temperature: {temperature}, Humidity {humidity}".format(
            temperature="{0:.2f}".format(self._temperature),
            humidity="{0:.2f}".format(self._humidity))

    def __iter__(self):  # must return an iterator
        """ DummySensor iterates through readings """
        return self

    def next(self):
        """ Get next reading """
        if self.read():
            raise StopIteration
        return dict(
            temperature=float('{0:.2f}'.format(self._temperature)),
            humidity=float('{0:.2f}'.format(self._humidity)))

    @property
    def temperature(self):
        """ temperature """
        if self._temperature is None:
            self.read()
        return self._temperature

    @property
    def humidity(self):
        """ humidity """
        if self._humidity is None:
            self.read()
        return self._humidity

    def get_measurement(self):
        """ Gets the temperature and humidity """
        #
        # Resetting these values ensures old measurements aren't mistaken for new measurements
        #
        self._temperature = None
        self._humidity = None

        temperature = None
        humidity = None

        #
        # Begin sensor measurement code
        #

        temperature = self.sensor.get_temperature()

        humidity = self.sensor.get_humidity()

        #
        # End sensor measurement code
        #

        #
        # Unit conversions
        # A conversion may be specified for each measurement, if more than one unit exists for that particular measurement
        #

        # Temperature is returned in C, but it may be converted to another unit (e.g. K, F)
        temperature = convert_units(
            'temperature', 'C', self.convert_to_unit,
            temperature)

        # Humidity is returned in percent, but it may be converted to another specified unit (e.g. decimal)
        humidity = convert_units(
            'humidity', 'percent', self.convert_to_unit,
            humidity)

        return temperature, humidity

    def read(self):
        """
        Takes a reading and updates the self._temperature and self._humidity values

        :returns: None on success or 1 on error
        """
        try:
            #
            # These measurements must be in the same order as the returned tuple from get_measurement()
            #
            self._temperature, self._humidity = self.get_measurement()
            if self._temperature is not None:
                return  # success - no errors
        except Exception as e:
            self.logger.exception(
                "{cls} raised an exception when taking a reading: "
                "{err}".format(cls=type(self).__name__, err=e))
        return 1
