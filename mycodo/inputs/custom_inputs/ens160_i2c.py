# coding=utf-8
"""
Custom Input: ENS160 Gas Sensor (I2C via Adafruit CircuitPython)

This custom Input reads eCO2 (ppm) and TVOC (ppb) from the ScioSense/ENSO ENS160
sensor using the Adafruit CircuitPython ENS160 library and Adafruit-extended-bus
for selecting the I2C bus by number.

Installation notes:
- Declare and install dependencies from the Mycodo UI before activating this Input.
- Wire the sensor to your device's I2C interface and select the correct I2C bus
  and address (default address is typically 0x53 for many ENS160 breakouts; check
  your board's documentation).

References:
- Adafruit ENS160 library: https://github.com/adafruit/Adafruit_CircuitPython_ENS160
- Product Learn Guide: https://learn.adafruit.com

This module follows patterns used by other CircuitPython-based inputs in Mycodo.
"""

import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements: mirror common gas sensor IDs used in other inputs (e.g., CCS811)
# 0: eCO2 in ppm (measurement ID: 'co2')
# 1: TVOC in ppb (measurement ID: 'voc')
# 2: AQI as a unitless index (measurement ID: 'unitless')
measurements_dict = {
    0: {
        'measurement': 'co2',
        'unit': 'ppm'
    },
    1: {
        'measurement': 'voc',
        'unit': 'ppb'
    },
    2: {
        'measurement': 'aqi',
        'unit': 'index'
    }
}

INPUT_INFORMATION = {
    'input_name_unique': 'ENS160_CP',
    'input_manufacturer': 'ScioSense',
    'input_name': 'ENS160 (CO2/VOC/AQI)',
    'input_name_short': 'ENS160',
    'input_library': 'Adafruit_CircuitPython_ENS160',
    'measurements_name': 'CO2/VOC/AQI',
    'measurements_dict': measurements_dict,

    'message': 'Reads eCO2 (ppm) and TVOC (ppb) from the ENS160 over I2C. '
               'Optionally configure temperature/humidity compensation via the Adafruit API by customizing this module.',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        # Extended I2C bus selection by bus number
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        # ENS160 CircuitPython library
        ('pip-pypi', 'adafruit_ens160', 'adafruit-circuitpython-ens160==1.1.13')
    ],

    'interfaces': ['I2C'],
    # Common default address for ENS160 breakouts (verify for your board)
    'i2c_location': ['0x53', '0x52'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """ENS160 sensor support class (I2C, Adafruit CircuitPython)."""

    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            # Attempt to initialize immediately so activation can start reading
            self.try_initialize()

    def initialize(self):
        # Import CircuitPython libraries at runtime to avoid import errors during discovery
        from adafruit_ens160 import ENS160
        from adafruit_extended_bus import ExtendedI2C

        # Create sensor with selected bus and address from Mycodo's Input config
        i2c = ExtendedI2C(self.input_dev.i2c_bus)
        address = int(str(self.input_dev.i2c_location), 16)
        self.sensor = ENS160(i2c, address=address)

        # ENS160 supports operation modes; default is standard mode. If needed:
        # self.sensor.operation_mode = 0x02  # Standard mode
        # Optionally set temperature/humidity compensation if you have references:
        # self.sensor.temperature_compensation = 25.0
        # self.sensor.humidity_compensation = 50.0

    def get_measurement(self):
        """Gets the eCO2 and TVOC measurements from the sensor."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        # Prepare fresh return dict
        self.return_dict = copy.deepcopy(measurements_dict)

        # Read values from the sensor. Library properties expected: .eco2, .tvoc
        try:
            if self.is_enabled(0):
                self.value_set(0, self.sensor.eco2)

            if self.is_enabled(1):
                self.value_set(1, self.sensor.tvoc)

            # AQI (Air Quality Index) as a unitless index
            try:
                aqi_val = getattr(self.sensor, 'aqi', None)
                if aqi_val is None:
                    aqi_val = getattr(self.sensor, 'AQI', None)
            except Exception:
                aqi_val = None

            if aqi_val is not None and self.is_enabled(2):
                self.value_set(2, aqi_val)

            return self.return_dict
        except Exception as exc:
            self.logger.error(f"Exception reading ENS160: {exc}")
            return
