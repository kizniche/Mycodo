# coding=utf-8
import copy

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
# See the inputs directory for examples of working modules.
# The following link provides the full list of options with descriptions:
# https://github.com/kizniche/Mycodo/blob/single_file_input_modules/mycodo/inputs/examples/example_all_options_temperature.py
INPUT_INFORMATION = {
    'input_name_unique': 'SCD30',
    'input_manufacturer': 'Sensirion',
    'input_name': 'SCD30',
    'input_library': 'scd30_i2c',
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
        ('pip-pypi', 'scd30_i2c', 'scd30-i2c==0.0.6')
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
        }
    ],

    'custom_options': [
        {
            'type': 'message',
            'default_value': 'Automatic Self Ccalibration (ASC): To work correctly, the sensor must be on and active for 7 days after enabling ASC, and exposed to fresh air for at least 1 hour per day. Consult the manufacturer’s documentation for more information.',
        },
        {
            'id': 'enable_self_calibration',
            'type': 'bool',
            'default_value': False,
            'name': 'Enable Automatic Self Calibration',
        }
    ]
}


class InputModule(AbstractInput):
    """Input support class."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.enable_self_calibration = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        from scd30_i2c import SCD30

        self.sensor = SCD30()

        self.sensor.set_auto_self_calibration(self.enable_self_calibration)

    def get_measurement(self):
        """Measures CO2, temperature and humidity."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.sensor.get_data_ready():
            m = self.sensor.read_measurement()
            if m is not None:
                co2 = m[0]
                temperature = m[1]
                humidity = m[2]

                if self.is_enabled(0):
                    self.value_set(0, co2)

                if self.is_enabled(1):
                    self.value_set(1, temperature)

                if self.is_enabled(2):
                    self.value_set(2, humidity)

                if self.is_enabled(3) and self.is_enabled(1) and self.is_enabled(2):
                    self.value_set(3, calculate_dewpoint(self.value_get(1), self.value_get(2)))

                if self.is_enabled(4) and self.is_enabled(1) and self.is_enabled(2):
                    self.value_set(4, calculate_vapor_pressure_deficit(self.value_get(1), self.value_get(2)))

        return self.return_dict

    def soft_reset(self, args_dict):
        if self.sensor:
            self.sensor.soft_reset()
