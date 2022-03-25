# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'temperature',
        'unit': 'C'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'MCP9808',
    'input_manufacturer': 'Microchip',
    'input_name': 'MCP9808',
    'input_library': 'Adafruit_MCP9808',
    'measurements_name': 'Temperature',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.microchip.com/wwwproducts/en/en556182',
    'url_datasheet': 'http://ww1.microchip.com/downloads/en/DeviceDoc/MCP9808-0.5C-Maximum-Accuracy-Digital-Temperature-Sensor-Data-Sheet-DS20005095B.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/1782',

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_GPIO', 'Adafruit-GPIO==1.0.3'),
        ('pip-pypi', 'Adafruit_MCP9808', 'git+https://github.com/adafruit/Adafruit_Python_MCP9808.git'),
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x18', '0x19', '0x1a', '0x1b', '0x1c', '0x1d', '0x1e', '0x1f'],
    'i2c_address_editable': False,

    'options_enabled': [
        'i2c_location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface']
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the MCP9808's temperature."""
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        """Initialize the MCP9808 sensor class."""
        from Adafruit_MCP9808 import MCP9808

        self.sensor = MCP9808.MCP9808(
            address=int(str(self.input_dev.i2c_location), 16),
            busnum=self.input_dev.i2c_bus)
        self.sensor.begin()

    def get_measurement(self):
        """Get measurements and store in the database."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        try:
            self.value_set(0, self.sensor.readTempC())
            return self.return_dict
        except Exception as msg:
            self.logger.exception("Input read failure: {}".format(msg))
