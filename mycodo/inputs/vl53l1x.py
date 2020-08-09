# coding=utf-8
import time

import copy
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
    'input_name_unique': 'VL53L1X',
    'input_manufacturer': 'STMicroelectronics',
    'input_name': 'VL53L1X',
    'input_library': 'VL53L1X',
    'measurements_name': 'Millimeter (Time-of-Flight Distance)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.st.com/en/imaging-and-photonics-solutions/vl53l0x.html',
    'url_datasheet': 'https://www.st.com/resource/en/datasheet/vl53l0x.pdf',
    'url_product_purchase': [
        'https://www.adafruit.com/product/3317',
        'https://www.pololu.com/product/2490'
    ],

    'message': 'Notes when setting a custom timing budget: A higher timing budget results in greater measurement accuracy, but also a higher power consumption. The inter measurement period must be >= the timing budget, otherwise it will be double the expected value.',

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'smbus2', 'smbus2'),
        ('pip-pypi', 'VL53L1X', 'vl53l1x')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x52'],
    'i2c_address_editable': True,

    'custom_options': [
        {
            'id': 'range',
            'type': 'select',
            'default_value': '1',
            'options_select': [
                ('1', 'Short Range'),
                ('2', 'Medium Range'),
                ('3', 'Long Range'),
                ('0', 'Custom Timing Budget')
            ],
            'name': lazy_gettext('Range'),
            'phrase': lazy_gettext('Select a range or select to set a custom Timing Budget and Inter Measurement Period.')
        },
        {
            'id': 'timing_budget',
            'type': 'integer',
            'default_value': 66000,
            'name': lazy_gettext('Timing Budget (microseconds)'),
            'phrase': lazy_gettext('Set the timing budget. Must be less than or equal to the Inter Measurement Period.')
        },
        {
            'id': 'inter_measurement_period',
            'type': 'integer',
            'default_value': 70,
            'name': lazy_gettext('Inter Measurement Period (milliseconds)'),
            'phrase': lazy_gettext('Set the Inter Measurement Period')
        }
    ],

    'custom_actions_message':
        'The I2C address of the sensor can be changed. Enter a new address in the 0xYY format '
        '(e.g. 0x22, 0x50), then press Set I2C Address. Remember to deactivate the Input and '
        'change the I2C address option after setting the new address.',

    'custom_actions': [
        {
            'id': 'new_i2c_address',
            'type': 'text',
            'default_value': '0x52',
            'name': lazy_gettext('New I2C Address'),
            'phrase': 'The new I2C to set the sensor to'
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
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.setting_i2c = False
        self.measuring = False

        self.range = None
        self.timing_budget = None
        self.inter_measurement_period = None
        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            self.initialize_input()

    def initialize_input(self):
        import VL53L1X

        self.VL53L1X = VL53L1X
        self.i2c_bus = self.input_dev.i2c_bus

        self.sensor = self.VL53L1X.VL53L1X(
            i2c_bus=self.i2c_bus,
            i2c_address=int(str(self.input_dev.i2c_location), 16))
        self.sensor.open()

        if self.range == '0':
            self.sensor.set_timing(self.timing_budget, self.inter_measurement_period)
            self.sensor.start_ranging(0)
        else:
            self.sensor.start_ranging(int(self.range))

    def get_measurement(self):
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        while self.setting_i2c:
            time.sleep(0.1)
        self.measuring = True

        self.value_set(0, self.sensor.get_distance())

        self.measuring = False

        return self.return_dict

    def set_i2c_address(self, args_dict):
        while self.measuring:
            time.sleep(0.1)
        self.setting_i2c = True

        self.sensor.stop_ranging()
        self.sensor.close()
        if 'new_i2c_address' not in args_dict:
            self.logger.error("Cannot set new I2C address without an I2C address")
            return
        try:
            i2c_address = int(str(args_dict['new_i2c_address']), 16)
            self.sensor.change_address(i2c_address)
            self.sensor = self.VL53L1X.VL53L1X(
                i2c_bus=self.i2c_bus,
                i2c_address=i2c_address)
            self.logger.info("Sensor I2C address set to {add}. Command executed: sensor.change_address({a_int})".format(
                    add=args_dict['new_i2c_address'], a_int=i2c_address))
        except:
            self.logger.error("Could not parse I2C address: {}. Ensure it's entered in the correct format.".format(
                    args_dict['new_i2c_address']))
        finally:
            self.sensor.open()
            self.sensor.start_ranging(self.timing_budget)
            self.setting_i2c = False

    def stop_input(self):
        """ Called when Input is deactivated """
        self.sensor.stop_ranging()
        self.sensor.close()
        self.running = False
