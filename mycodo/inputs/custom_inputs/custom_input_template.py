# coding=utf-8
"""
Custom Input Module Template for Mycodo

How to use this file:
- Copy this file to a new filename (e.g., my_sensor.py) in the same directory.
- Follow inline instructions and the official guide:
  https://github.com/kizniche/Mycodo/wiki/Building-a-Custom-Input-Module

This template is safe to be present in the system because it has no side effects at import time.
Only import external dependencies within initialize().
"""

import copy

from mycodo.inputs.base_input import AbstractInput

# ---------------------------------------------------------------------------
# 1) Define your measurements
#    Keys 0,1,2,.. are channels; map each to a measurement ID and unit ID.
#    Measurement and Unit IDs must match those listed in the Mycodo Measurement config.
#    See mycodo/inputs/examples for full examples.
# ---------------------------------------------------------------------------
measurements_dict = {
    0: {
        'measurement': 'temperature',  # e.g., 'temperature'
        'unit': 'C'                     # e.g., 'C' for Celsius
    }
}

# ---------------------------------------------------------------------------
# 2) Describe your Input using INPUT_INFORMATION
#    - input_name_unique MUST be unique across all Inputs.
#    - Only import external modules inside initialize() to avoid discovery-time errors.
#    - Add dependencies in dependencies_module if needed.
# ---------------------------------------------------------------------------
INPUT_INFORMATION = {
    # Unique identifier (must be globally unique across inputs)
    'input_name_unique': 'CUSTOM_INPUT_TEMPLATE',

    # Descriptions shown in the UI
    'input_manufacturer': 'Your Company',
    'input_name': 'Custom Input Template',
    'input_name_short': 'Custom Template',
    'input_library': 'your-library-name',  # Optional descriptive string

    # Measurements provided by this Input
    'measurements_name': 'Example Temperature',
    'measurements_dict': measurements_dict,

    # If multiple measurements are produced at the same instant, set True
    'measurements_use_same_timestamp': True,

    # Built-in UI options visibility
    # Common entries: 'interface', 'i2c_location', 'period', 'pre_output', etc.
    'options_enabled': [
        'period'
    ],
    'options_disabled': [
        'interface',
        'i2c_location'
    ],

    # List Python dependencies if your input needs them
    # Example: [('pip-pypi', 'adafruit-circuitpython-bme280', 'adafruit-circuitpython-bme280==2.6.20')]
    'dependencies_module': [],

    # Optional: add custom options exposed on the Input options page
    # Access these as attributes on self after setup_custom_options() in __init__
    'custom_options': [
        {
            'id': 'example_integer',
            'type': 'integer',
            'default_value': 42,
            'name': 'Example Integer',
            'phrase': 'An example custom option.'
        }
    ],
}


class InputModule(AbstractInput):
    """Skeleton Input module.

    Implement your hardware/client logic in initialize() and get_measurement().
    """

    def __init__(self, input_dev, testing=False):
        # Initialize base class and logger
        super().__init__(input_dev, testing=testing, name=__name__)

        # Initialize your instance variables here (do not import external libs yet)
        self.example_integer = None  # from custom_options
        self.interface = None
        self.i2c_address = None
        self.i2c_bus = None

        if not testing:
            # Load custom option defaults/user values into self.<option_id>
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)

    def initialize(self):
        """Import dependencies and initialize hardware/clients here."""
        # Example: import external libs here (safe during runtime, not import time)
        # import some_library

        # Grab commonly-used properties from the DB-saved Input configuration
        self.interface = self.input_dev.interface
        self.i2c_address = getattr(self.input_dev, 'i2c_location', None)
        self.i2c_bus = getattr(self.input_dev, 'i2c_bus', None)

        # Initialize your hardware or network clients here
        # For example:
        # if self.interface == 'I2C' and self.i2c_address:
        #     addr_int = int(str(self.i2c_address), 16)
        #     self.sensor = some_library.Sensor(i2c_address=addr_int, i2c_bus=self.i2c_bus)
        pass

    def get_measurement(self):
        """Acquire data and return a measurements dictionary or None on error.

        Use self.value_set(channel, value[, timestamp]) to populate self.return_dict.
        Always guard with self.is_enabled(channel) before computing/storing a measurement.
        """
        # Start from a clean copy of the measurement schema
        self.return_dict = copy.deepcopy(measurements_dict)

        try:
            # Example: Acquire a single value (replace with real sensor/client calls)
            # value = self.sensor.read_temperature_c()
            value = float(self.example_integer)  # Dummy usage of custom option

            if self.is_enabled(0):
                self.value_set(0, value)

            # Optionally log details
            self.logger.debug(f"Measurement dict: {self.return_dict}")

            return self.return_dict
        except Exception as exc:
            # Any exception here will be logged and the read loop will continue
            self.logger.error(f"Exception acquiring measurement: {exc}")
            # Return None to indicate failure
            return None
