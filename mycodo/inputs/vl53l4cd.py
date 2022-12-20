# coding=utf-8
import copy
import time

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput

# Measurements
measurements_dict = {
    0: {
        'measurement': 'length',
        'unit': 'mm'
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'VL53L4CD',
    'input_manufacturer': 'STMicroelectronics',
    'input_name': 'VL53L4CD',
    'input_library': 'Adafruit-CircuitPython-VL53l4CD',
    'measurements_name': 'Millimeter (Time-of-Flight Distance)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.st.com/en/imaging-and-photonics-solutions/VL53L4CD.html',
    'url_datasheet': 'https://www.st.com/resource/en/datasheet/VL53L4CDpdf',
    'url_product_purchase': 'https://www.adafruit.com/product/3317',

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
        ('pip-pypi', 'adafruit_vl53l4cd', 'adafruit-circuitpython-vl53l4cd==1.1.4')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x29'],
    'i2c_address_editable': True,

    'custom_options': [
        {
            'id': 'timing_budget',
            'type': 'integer',
            'default_value': 50,
            'name': 'Timing Budget (ms)',
            'phrase': 'Set the timing budget between 10 to 200 ms. A longer duration yields a more accurate measurement.'
        },
        {
            'id': 'inter_measurement',
            'type': 'integer',
            'default_value': 0,
            'name': 'Inter-Measurement Period (ms)',
            'phrase': 'Valid range between Timing Budget and 5000 ms (0 to disable)'
        }
    ],

    'custom_commands': [
        {
            'type': 'message',
            'default_value': 'The I2C address of the sensor can be changed. Enter a new address in the 0xYY format '
                             '(e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate the Input and '
                             'change the I2C address option after setting the new address.'
        },
        {
            'id': 'new_i2c_address',
            'type': 'text',
            'default_value': '0x29',
            'name': lazy_gettext('New I2C Address'),
            'phrase': lazy_gettext('The new I2C to set the device to')
        },
        {
            'id': 'set_i2c_address',
            'type': 'button',
            'name': lazy_gettext('Set I2C Address')
        }
    ]
}


class InputModule(AbstractInput):
    """
    A sensor support class that measures the sensor
    """
    def __init__(self, input_dev, testing=False):
        super().__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.setting_i2c = False
        self.measuring = False

        self.timing_budget = None
        self.inter_measurement = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.try_initialize()

    def initialize(self):
        import adafruit_vl53l4cd
        from adafruit_extended_bus import ExtendedI2C

        self.sensor = adafruit_vl53l4cd.VL53L4CD(
            ExtendedI2C(self.input_dev.i2c_bus),
            address=int(str(self.input_dev.i2c_location), 16))

        if self.timing_budget < 10 or self.timing_budget > 200:
            self.logger.error(f"Invalid Timing Budget: '{self.timing_budget}'. Must be between 10 and 200 ms")
        else:
            self.sensor.timing_budget = self.timing_budget
            self.logger.debug(f"Set Timing Budget to {self.timing_budget} ms")

        if self.inter_measurement:
            if self.inter_measurement < self.timing_budget:
                self.logger.error("Inter-measurement period can not be less than timing budget")
            else:
                self.sensor.stop_ranging()
                self.sensor.inter_measurement(self.inter_measurement)
                self.logger.debug(f"Set Inter Measurement to {self.inter_measurement} ms")

    def get_measurement(self):
        if not self.sensor:
            self.logger.error("Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info.")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        while self.setting_i2c:
            time.sleep(0.1)

        self.sensor.start_ranging()
        self.sensor.clear_interrupt()
        distance = self.sensor.distance * 10  # convert cm to to mm
        
        self.logger.debug(f"Timing Budget: {self.sensor.timing_budget} ms")
        self.logger.debug(f"Inter Measurement: {self.sensor.inter_measurement} ms")
        self.logger.debug(f"Distance: {distance} mm")

        self.value_set(0, distance)
        self.sensor.stop_ranging()

        return self.return_dict

    def set_i2c_address(self, args_dict):
        while self.measuring:
            time.sleep(0.1)
        self.setting_i2c = True

        if 'new_i2c_address' not in args_dict:
            self.logger.error("Cannot set new I2C address without an I2C address")
            return
        try:
            self.sensor.stop_ranging()
            i2c_address = int(str(args_dict['new_i2c_address']), 16)
            self.sensor.set_address(i2c_address)
            self.logger.info(f"Sensor I2C address set to {args_dict['new_i2c_address']}. Command executed: sensor.set_address({i2c_address})")
        except:
            self.logger.error(f"Could not parse I2C address: '{args_dict['new_i2c_address']}'. Ensure it's entered in the correct format.")
        finally:
            self.setting_i2c = False
