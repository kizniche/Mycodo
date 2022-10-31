# coding=utf-8
import copy
import time

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

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'SCD4x_CIRCUITPYTHON',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SCD-4x (40, 41)',
    'input_name_short': 'SCD-4x',
    'input_library': 'Adafruit_CircuitPython_SCD4x',
    'measurements_name': 'CO2/Temperature/Humidity',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.sensirion.com/en/environmental-sensors/carbon-dioxide-sensors/carbon-dioxide-sensor-scd4x/',

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
        ('pip-pypi', 'adafruit_scd4x', 'adafruit-circuitpython-scd4x==1.2.2')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x62'],
    'i2c_address_editable': False,

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """You can force the CO2 calibration for a specific CO2 concentration value (in ppmv). The sensor needs to be active for at least 3 minutes prior to calibration."""
        },
        {
            'id': 'co2_concentration',
            'type': 'float',
            'default_value': 400.0,
            'name': 'CO2 Concentration (ppmv)',
            'phrase': 'Calibrate to this CO2 concentration that the sensor is being exposed to (in ppmv)'
        },
        {
            'id': 'co2_calibration',
            'type': 'button',
            'name': 'Calibrate CO2'
        }
    ],

    'custom_options': [
        {
            'id': 'temperature_offset',
            'type': 'float',
            'default_value': 4.0,
            'required': True,
            'name': 'Temperature Offset',
            'phrase': 'Set the sensor temperature offset'
        },
        {
            'id': 'altitude',
            'type': 'integer',
            'default_value': 0,
            'required': True,
            'name': 'Altitude (m)',
            'phrase': 'Set the sensor altitude (meters)'
        },
        {
            'id': 'self_calibration_enabled',
            'type': 'bool',
            'default_value': False,
            'name': 'Automatic Self-Calibration',
            'phrase': 'Set the sensor automatic self-calibration'
        },
        {
            'id': 'persist_settings',
            'type': 'bool',
            'default_value': True,
            'name': 'Persist Settings',
            'phrase': 'Settings will persist after powering off'
        },
    ]
}


class InputModule(AbstractInput):
    """A sensor support class that measures."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.temperature_offset = None
        self.altitude = None
        self.self_calibration_enabled = None
        self.persist_settings = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import adafruit_scd4x
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_scd4x.SCD4X(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=int(str(self.input_dev.i2c_location), 16))

        self.logger.debug("Serial number: {}".format([hex(i) for i in self.sensor.serial_number]))

        if self.sensor.temperature_offset != self.temperature_offset:
            self.sensor.temperature_offset = self.temperature_offset
        self.logger.debug("Temperature offset: {}".format(self.sensor.temperature_offset))

        if self.sensor.altitude != self.altitude:
            self.sensor.altitude = self.altitude
        self.logger.debug("Altitude: {} meters above sea level".format(self.sensor.altitude))

        if self.sensor.self_calibration_enabled != self.self_calibration_enabled:
            self.sensor.self_calibration_enabled = self.self_calibration_enabled
        self.logger.debug("Self-calibration enabled: {}".format(self.sensor.self_calibration_enabled))

        if self.persist_settings:
            self.sensor.persist_settings()

        self.sensor.start_periodic_measurement()

    def get_measurement(self):
        """Gets the measurements."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        timer = time.time() + 10
        while not self.sensor.data_ready and time.time() < timer:
            time.sleep(1)

        if self.sensor.data_ready:
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
        else:
            self.logger.error("data_ready is False")

    def stop_input(self):
        self.running = False
        self.sensor.stop_periodic_measurement()

    def co2_calibration(self, args_dict):
        if 'co2_concentration' not in args_dict or not args_dict['co2_concentration']:
            self.logger.error("CO2 Concentration required")
            return
        try:
            self.sensor.force_calibration(int(args_dict['co2_concentration']))
            self.sensor.start_periodic_measurement()
        except Exception as err:
            self.logger.error(
                "Error setting CO2 Concentration: {}".format(err))
