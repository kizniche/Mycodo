# coding=utf-8
import copy
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.inputs.sensorutils import calculate_dewpoint
from mycodo.inputs.sensorutils import calculate_vapor_pressure_deficit

# Measurements
measurements_dict = {
    0: {
        'measurement': 'co2',
        'unit': 'ppm'
    },
    1: {
        'measurement': 'temperature',
        'unit': 'C'
    },
    2: {
        'measurement': 'humidity',
        'unit': 'percent'
    },
    3: {
        'measurement': 'dewpoint',
        'unit': 'C'
    },
    4: {
        'measurement': 'vapor_pressure_deficit',
        'unit': 'Pa'
    }
}

INPUT_INFORMATION = {
    'input_name_unique': 'SCD30_CIRCUITPYTHON',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SCD30',
    'input_library': 'Adafruit_CircuitPython_SCD30',
    'measurements_name': 'CO2/Humidity/Temperature',
    'measurements_dict': measurements_dict,
    'measurements_use_same_timestamp': True,

    'url_manufacturer': 'https://www.sensirion.com/en/environmental-sensors/carbon-dioxide-sensors/carbon-dioxide-sensors-co2/',
    'url_datasheet': 'https://www.sensirion.com/fileadmin/user_upload/customers/sensirion/Dokumente/9.5_CO2/Sensirion_CO2_Sensors_SCD30_Datasheet.pdf',
    'url_product_purchase': [
        'https://www.sparkfun.com/products/15112',
        'https://www.futureelectronics.com/p/4115766'
    ],

    'options_enabled': [
        'measurements_select',
        'i2c_location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'adafruit_scd30', 'adafruit-circuitPython-scd30==2.2.1')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x61'],
    'i2c_address_editable': False,

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """A soft reset restores factory default values."""
        },
        {
            'id': 'soft_reset',
            'type': 'button',
            'name': 'Soft Reset'
        },
        {
            'type': 'message',
            'default_value': """Forced Re-Calibration: The SCD-30 is placed in an environment with a known CO2 concentration, this concentration value is entered in the CO2 Concentration (ppmv) field, then the Foce Calibration button is pressed. But how do you come up with that known value? That is a caveat of this approach and Sensirion suggests three approaches: 1. Using a separate secondary calibrated CO2 sensor to provide the value. 2. Exposing the SCD-30 to a controlled environment with a known value. 3. Exposing the SCD-30 to fresh outside air and using a value of 400 ppm."""
        },
        {
            'id': 'force_recalibration_ppmv',
            'type': 'integer',
            'default_value': 800,
            'name': 'CO2 Concentration (ppmv)',
            'phrase': 'The CO2 concentration of the sensor environment when forcing calibration'
        },
        {
            'id': 'force_recalibration',
            'type': 'button',
            'name': 'Force Recalibration'
        }
    ],

    'custom_options': [
        {
            'type': 'message',
            'default_value': 'I2C Frequency: The SCD-30 has temperamental I2C with clock stretching. The datasheet recommends starting at 50,000 Hz.'
        },
        {
            'id': 'i2c_frequency',
            'type': 'integer',
            'default_value': 50000,
            'name': 'I2C Frequency (Hz)',
        },
        {
            'type': 'message',
            'default_value': 'Automatic Self Ccalibration (ASC): To work correctly, the sensor must be on and active for 7 days after enabling ASC, and exposed to fresh air for at least 1 hour per day. Consult the manufacturer’s documentation for more information.',
        },
        {
            'id': 'enable_self_calibration',
            'type': 'bool',
            'default_value': False,
            'name': 'Enable Automatic Self Calibration',
        },
        {
            'type': 'message',
            'default_value': 'Temperature Offset: Specifies the offset to be added to the reported measurements to account for a bias in the measured signal. Must be a positive value, and will reduce the recorded temperature by that amount. Give the sensor adequate time to acclimate after setting this value. Value is in degrees Celsius with a resolution of 0.01 degrees and a maximum value of 655.35 C.',
        },
        {
            'id': 'temperature_offset',
            'type': 'float',
            'default_value': 0.0,
            'name': lazy_gettext("Temperature Offset"),
        },
        {
            'type': 'message',
            'default_value': 'Ambient Air Pressure (mBar): Specify the ambient air pressure at the measurement location in mBar. Setting this value adjusts the CO2 measurement calculations to account for the air pressure’s effect on readings. Values must be in mBar, from 700 to 1200 mBar.'
        },
        {
            'id': 'ambient_pressure',
            'type': 'integer',
            'default_value': 1200,
            'name': 'Ambient Air Pressure (mBar)',
        },
        {
            'type': 'message',
            'default_value': 'Altitude: Specifies the altitude at the measurement location in meters above sea level. Setting this value adjusts the CO2 measurement calculations to account for the air pressure’s effect on readings.'
        },
        {
            'id': 'altitude',
            'type': 'integer',
            'default_value': 100,
            'name': 'Altitude (m)',
        },
    ]
}


class InputModule(AbstractInput):
    """Input support class."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.i2c_frequency = None
        self.enable_self_calibration = None
        self.temperature_offset = None
        self.ambient_pressure = None
        self.altitude = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        from adafruit_extended_bus import ExtendedI2C
        import adafruit_scd30

        self.sensor = adafruit_scd30.SCD30(
            ExtendedI2C(self.input_dev.i2c_bus, frequency=self.i2c_frequency),
            address=int(str(self.input_dev.i2c_location), 16))

        if self.sensor.self_calibration_enabled != self.enable_self_calibration:
            self.sensor.self_calibration_enabled = self.enable_self_calibration

        if self.sensor.temperature_offset != self.temperature_offset:
            self.sensor.temperature_offset = self.temperature_offset

        if self.sensor.ambient_pressure != self.ambient_pressure:
            self.sensor.ambient_pressure = self.ambient_pressure

        if self.sensor.altitude != self.altitude:
            self.sensor.altitude = self.altitude

    def get_measurement(self):
        """Measures CO2, temperature and humidity."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.sensor.data_available:
            if self.is_enabled(0):
                self.value_set(0, self.sensor.CO2)

            if self.is_enabled(1):
                self.value_set(1, self.sensor.temperature)

            if self.is_enabled(2):
                self.value_set(2, self.sensor.relative_humidity)

            if self.is_enabled(3) and self.is_enabled(1) and self.is_enabled(2):
                self.value_set(3, calculate_dewpoint(self.value_get(1), self.value_get(2)))

            if self.is_enabled(4) and self.is_enabled(1) and self.is_enabled(2):
                self.value_set(4, calculate_vapor_pressure_deficit(self.value_get(1), self.value_get(2)))

        return self.return_dict

    def soft_reset(self, args_dict):
        if self.sensor:
            self.sensor.reset()

    def force_recalibration(self, args_dict):
        if 'force_recalibration_ppmv' not in args_dict:
            self.logger.error("Cannot calibrate without CO2 Concentration (ppmv)")
            return
        if self.sensor:
            self.sensor.forced_recalibration_reference = args_dict['force_recalibration_ppmv']
