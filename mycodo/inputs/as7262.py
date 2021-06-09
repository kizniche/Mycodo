# coding=utf-8
import copy

from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput
from mycodo.utils.constraints_pass import constraints_pass_positive_value

# Measurements
measurements_dict = {
    0: {
        'measurement': 'adc',
        'unit': 'unitless',
        'name': '450 nm (red)'
    },
    1: {
        'measurement': 'adc',
        'unit': 'unitless',
        'name': '500 nm (orange)',
    },
    2: {
        'measurement': 'adc',
        'unit': 'unitless',
        'name': '550 nm (yellow)',
    },
    3: {
        'measurement': 'adc',
        'unit': 'unitless',
        'name': '570 nm (green)',
    },
    4: {
        'measurement': 'adc',
        'unit': 'unitless',
        'name': '600 nm (blue)',
    },
    5: {
        'measurement': 'adc',
        'unit': 'unitless',
        'name': '650 nm (violet)',
    }
}

# Input information
INPUT_INFORMATION = {
    'input_name_unique': 'AS7262',
    'input_manufacturer': 'AMS',
    'input_name': 'AS7262',
    'input_library': 'as7262',
    'measurements_name': 'Light at 450, 500, 550, 570, 600, 650 nm',
    'measurements_dict': measurements_dict,
    'url_manufacturer': 'https://ams.com/as7262',
    'url_datasheet': 'https://ams.com/documents/20143/36005/AS7262_DS000486_2-00.pdf/0031f605-5629-e030-73b2-f365fd36a43b',
    'url_product_purchase': 'https://www.sparkfun.com/products/14347',

    'options_enabled': [
        'period',
        'pre_output'
    ],
    'options_disabled': [
        'interface',
        'i2c_location'
    ],

    'dependencies_module': [
        ('pip-pypi', 'as7262', 'as7262==0.1.0'),
    ],

    'interfaces': ['I2C'],
    'i2c_location': ['0x49'],
    'i2c_address_editable': False,

    'custom_options': [
        {
            'id': 'gain',
            'type': 'select',
            'default_value': '64',
            'options_select': [
                ('1', '1x'),
                ('3.7', '3.7x'),
                ('16', '16x'),
                ('64', '64x')
            ],
            'name': lazy_gettext('Gain'),
            'phrase': 'Set the sensor gain'
        },
        {
            'id': 'illumination_led_current',
            'type': 'select',
            'default_value': '12.5',
            'options_select': [
                ('12.5', '12.5 mA'),
                ('25', '25 mA'),
                ('50', '50 mA'),
                ('100', '100 mA')
            ],
            'name': 'Illumination LED Current',
            'phrase': 'Set the illumination LED current (milliamps)'
        },
        {
            'id': 'illumination_led_mode',
            'type': 'select',
            'default_value': '1',
            'options_select': [
                ('1', 'On'),
                ('0', 'Off')
            ],
            'name': 'Illumination LED Mode',
            'phrase': 'Turn the illumination LED on or off during a measurement'
        },
        {
            'id': 'indicator_led_current',
            'type': 'select',
            'default_value': '1',
            'options_select': [
                ('1', '1 mA'),
                ('2', '2 mA'),
                ('4', '4 mA'),
                ('8', '8 mA')
            ],
            'name': 'Indicator LED Current',
            'phrase': 'Set the indicator LED current (milliamps)'
        },
        {
            'id': 'indicator_led_mode',
            'type': 'select',
            'default_value': '1',
            'options_select': [
                ('1', 'On'),
                ('0', 'Off')
            ],
            'name': 'Indicator LED Mode',
            'phrase': 'Turn the indicator LED on or off during a measurement'
        },
        {
            'id': 'integration_time',
            'type': 'float',
            'default_value': 15.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Integration Time',
            'phrase': 'The integration time (0 - ~91 ms)'
        }
    ],
}


class InputModule(AbstractInput):
    """ A sensor support class that acquires measurements from the sensor """
    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.sensor = None

        self.gain = None
        self.illumination_led_current = None
        self.illumination_led_mode = None
        self.indicator_led_current = None
        self.indicator_led_mode = None
        self.integration_time = None

        if not testing:
            self.setup_custom_options(
                INPUT_INFORMATION['custom_options'], input_dev)
            self.initialize_input()

    def initialize_input(self):
        from as7262 import AS7262

        self.sensor = AS7262()

        hw_type, hw_version, fw_version = self.sensor.get_version()
        self.logger.info("AS7262: Hardware Type: {hwt}, Hardware Version: {hwv}, Firmware Version: {fwv}".format(
            hwt=hw_type, hwv=hw_version, fwv=fw_version))

        self.sensor.set_gain(float(self.gain))
        self.sensor.set_indicator_led_current(float(self.indicator_led_current))
        self.sensor.set_illumination_led_current(float(self.illumination_led_current))
        self.sensor.set_integration_time(self.integration_time)

    def get_measurement(self):
        """ Get measurements and store in the database """
        if not self.sensor:
            self.logger.error("Input not set up")
            return

        self.return_dict = copy.deepcopy(measurements_dict)

        self.sensor.set_measurement_mode(2)
        self.sensor.set_indicator_led(int(self.indicator_led_mode))
        self.sensor.set_illumination_led(int(self.illumination_led_mode))

        values = self.sensor.get_calibrated_values()

        self.sensor.set_measurement_mode(3)
        self.sensor.set_indicator_led(0)
        self.sensor.set_illumination_led(0)

        self.logger.debug(
            "450 nm (Red): {}, "
            "500 nm (Orange): {}, "
            "550 nm (Yellow): {}, "
            "570 nm (Green): {}, "
            "600 nm (Blue): {}, "
            "650 nm (Violet): {}".format(*values))

        for index, color_value in enumerate(values):
            self.value_set(index, color_value)

        return self.return_dict

    def stop_input(self):
        """ Called when Input is deactivated """
        self.sensor.set_measurement_mode(3)
        self.sensor.set_indicator_led(0)
        self.sensor.set_illumination_led(0)
        self.running = False
