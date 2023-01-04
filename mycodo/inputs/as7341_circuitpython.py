# coding=utf-8
import copy

from mycodo.inputs.base_input import AbstractInput

measurements_dict = {
    0: {"measurement": "light", "unit": "unitless", "name": "415nm"},
    1: {"measurement": "light", "unit": "unitless", "name": "445nm"},
    2: {"measurement": "light", "unit": "unitless", "name": "480nm"},
    3: {"measurement": "light", "unit": "unitless", "name": "515nm"},
    4: {"measurement": "light", "unit": "unitless", "name": "555nm"},
    5: {"measurement": "light", "unit": "unitless", "name": "590nm"},
    6: {"measurement": "light", "unit": "unitless", "name": "630nm"},
    7: {"measurement": "light", "unit": "unitless", "name": "680nm"},
    8: {"measurement": "light", "unit": "unitless", "name": "Clear"},
    9: {"measurement": "light", "unit": "unitless", "name": "NIR"},
}

# Input information
INPUT_INFORMATION = {
    "input_name_unique": "AS7341",
    "input_manufacturer": "ams",
    "input_name": "AS7341",
    "input_library": "Adafruit-CircuitPython-AS7341",
    "measurements_name": "Light",
    "measurements_dict": measurements_dict,
    "url_manufacturer": "https://ams.com/as7341",
    "url_datasheet": "https://ams.com/documents/20143/36005/AS7341_DS000504_3-00.pdf/5eca1f59-46e2-6fc5-daf5-d71ad90c9b2b",
    "url_product_purchase": [
        "https://www.adafruit.com/product/4698",
        "https://shop.pimoroni.com/products/adafruit-as7341-10-channel-light-color-sensor-breakout-stemma-qt-qwiic",
        "https://www.berrybase.de/adafruit-as7341-10-kanal-licht-und-farb-sensor-breakout",
    ],
    "options_enabled": ["i2c_location", "period", "pre_output"],
    "options_disabled": ["interface"],
    "dependencies_module": [
        ("pip-pypi", "adafruit_extended_bus", "adafruit-extended-bus==1.0.2"),
        ("pip-pypi", "adafruit_as7341", "adafruit-circuitpython-as7341==1.2.13"),
    ],
    "interfaces": ["I2C"],
    "i2c_location": ["0x39"],
    "i2c_address_editable": False,
}


class InputModule(AbstractInput):
    """A sensor support class that monitors the AS7341's light"""

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        import adafruit_as7341
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_as7341.AS7341(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=int(str(self.input_dev.i2c_location), 16),
        )

    def get_measurement(self):
        """Gets the intensities of light accross the visible spectrum"""
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        if self.is_enabled(0):
            self.value_set(0, self.sensor.channel_415nm)

        if self.is_enabled(1):
            self.value_set(1, self.sensor.channel_445nm)

        if self.is_enabled(2):
            self.value_set(2, self.sensor.channel_480nm)

        if self.is_enabled(3):
            self.value_set(3, self.sensor.channel_515nm)

        if self.is_enabled(4):
            self.value_set(4, self.sensor.channel_555nm)

        if self.is_enabled(5):
            self.value_set(5, self.sensor.channel_590nm)

        if self.is_enabled(6):
            self.value_set(6, self.sensor.channel_630nm)

        if self.is_enabled(7):
            self.value_set(7, self.sensor.channel_680nm)

        if self.is_enabled(8):
            self.value_set(8, self.sensor.channel_clear)

        if self.is_enabled(9):
            self.value_set(9, self.sensor.channel_nir)

        return self.return_dict
