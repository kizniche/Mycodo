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
    'input_name_unique': 'VL53L0X',
    'input_manufacturer': 'STMicroelectronics',
    'input_name': 'VL53L0X',
    'input_library': 'VL53L0X_rasp_python',
    'measurements_name': 'Millimeter (Time-of-Flight Distance)',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://www.st.com/en/imaging-and-photonics-solutions/vl53l0x.html',
    'url_datasheet': 'https://www.st.com/resource/en/datasheet/vl53l0x.pdf',
    'url_product_purchase': [
        'https://www.adafruit.com/product/3317',
        'https://www.pololu.com/product/2490'
    ],

    'options_enabled': [
        'i2c_location',
        'measurements_select',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'VL53L0X', 'git+https://github.com/grantramsay/VL53L0X_rasp_python.git')
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x52'],
    'i2c_address_editable': True,

    'custom_options': [
        {
            'id': 'timing_budget',
            'type': 'select',
            'default_value': '0',
            'options_select': [
                ('0', 'Good Accuracy (33 ms, 1.2 m range)'),
                ('1', 'Better Accuracy (66 ms, 1.2 m range)'),
                ('2', 'Best Accuracy (200 ms, 1.2 m range)'),
                ('3', 'Long Range (33 ms, 2 m)'),
                ('4', 'High Speed, Low Accuracy (20 ms, 1.2 m)')
            ],
            'name': 'Accuracy',
            'phrase': 'Set the accuracy. A longer measurement duration yields a more accurate measurement'
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
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None
        self.setting_i2c = False
        self.measuring = False

        self.timing_budget = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        import VL53L0X

        self.VL53L0X = VL53L0X
        self.i2c_bus = self.input_dev.i2c_bus

        self.sensor = self.VL53L0X.VL53L0X(
            i2c_bus=self.i2c_bus,
            i2c_address=int(str(self.input_dev.i2c_location), 16))
        self.sensor.open()

        # GOOD = 0  # 33 ms timing budget 1.2m range
        # BETTER = 1  # 66 ms timing budget 1.2m range
        # BEST = 2  # 200 ms 1.2m range
        # LONG_RANGE = 3  # 33 ms timing budget 2m range
        # HIGH_SPEED = 4  # 20 ms timing budget 1.2m range
        if self.timing_budget == '0':
            self.timing_budget = VL53L0X.Vl53l0xAccuracyMode.GOOD
        elif self.timing_budget == '1':
            self.timing_budget = VL53L0X.Vl53l0xAccuracyMode.BETTER
        elif self.timing_budget == '2':
            self.timing_budget = VL53L0X.Vl53l0xAccuracyMode.BEST
        elif self.timing_budget == '3':
            self.timing_budget = VL53L0X.Vl53l0xAccuracyMode.LONG_RANGE
        elif self.timing_budget == '4':
            self.timing_budget = VL53L0X.Vl53l0xAccuracyMode.HIGH_SPEED
        self.sensor.start_ranging(self.timing_budget)

    def get_measurement(self):
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        while self.setting_i2c:
            time.sleep(0.1)
        self.measuring = True

        length = self.sensor.get_distance()
        self.value_set(0, length)

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
            self.sensor = self.VL53L0X.VL53L0X(
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
