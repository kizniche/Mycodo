# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'co2',
        'unit': 'ppm'
    },
    1: {
        'measurement': 'voc',
        'unit': 'ppb'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'CCS811_CP',
    'input_manufacturer': 'AMS',
    'input_name': 'CCS811 (without Temperature)',
    'input_name_short': 'CCS881 (w/o temp)',
    'input_library': 'Adafruit_CircuitPython_CCS811',
    'measurements_name': 'CO2/VOC',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.sciosense.com/products/environmental-sensors/ccs811-gas-sensor-solution/',
    'url_datasheet': 'https://www.sciosense.com/wp-content/uploads/2020/01/CCS811-Datasheet.pdf',
    'url_additional': 'https://learn.adafruit.com/adafruit-ccs811-air-quality-sensor',
    'url_product_purchase': 'https://www.adafruit.com/product/3566',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'usb.core', 'pyusb==1.1.1'),
        ('pip-pypi', 'adafruit_extended_bus', 'Adafruit-extended-bus==1.0.2'),
        ('pip-pypi', 'adafruit_ccs811', 'adafruit-circuitpython-ccs811==1.3.4')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x5a', '0x5b'],
    'i2c_address_editable': False
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the CC2811's voc and co2
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.try_initialize()

    def initialize(self):
        import adafruit_ccs811
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_ccs811.CCS811(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=int(str(self.input_dev.i2c_location), 16))

    def get_measurement(self):
        """Gets the CO2, VOC, and temperature."""
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.eco2)

        if self.is_enabled(1):
            self.value_set(1, self.sensor.tvoc)

        return self.return_dict
