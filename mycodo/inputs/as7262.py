# coding=utf-8
from flask_babel import lazy_gettext

from mycodo.inputs.base_input import AbstractInput


def constraints_pass_positive_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_input


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

    'options_enabled': [
        'location',
        'period',
        'pre_output'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'as7262', 'as7262'),
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
            'phrase': lazy_gettext('Set the sensor gain')
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
            'name': lazy_gettext('Illumination LED Current'),
            'phrase': lazy_gettext('Set the illumination LED current (milliamps)')
        },
        {
            'id': 'illumination_led_mode',
            'type': 'select',
            'default_value': '1',
            'options_select': [
                ('1', 'On'),
                ('0', 'Off')
            ],
            'name': lazy_gettext('Illumination LED Mode'),
            'phrase': lazy_gettext('Turn the illumination LED on or off during a measurement')
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
            'name': lazy_gettext('Indicator LED Current'),
            'phrase': lazy_gettext('Set the indicator LED current (milliamps)')
        },
        {
            'id': 'indicator_led_mode',
            'type': 'select',
            'default_value': '1',
            'options_select': [
                ('1', 'On'),
                ('0', 'Off')
            ],
            'name': lazy_gettext('Indicator LED Mode'),
            'phrase': lazy_gettext('Turn the indicator LED on or off during a measurement')
        },
        {
            'id': 'integration_time',
            'type': 'float',
            'default_value': 15.0,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Integration Time'),
            'phrase': lazy_gettext('The integration time (0 - ~91 ms)')
        }
    ],
}


class InputModule(AbstractInput):
    """ A sensor support class that acquires measurements from the sensor """

    def __init__(self, input_dev, testing=False):
        super(InputModule, self).__init__(input_dev, testing=testing, name=__name__)

        self.gain = None
        self.illumination_led_current = None
        self.illumination_led_mode = None
        self.indicator_led_current = None
        self.indicator_led_mode = None
        self.integration_time = None

        self.setup_custom_options(
            INPUT_INFORMATION['custom_options'], input_dev)

        if not testing:
            from as7262 import AS7262

            self.location = input_dev.location

            self.sensor = AS7262()

            hw_type, hw_version, fw_version = self.sensor.get_version()
            self.logger.info(
                "AS7262: Hardware Type: {}, "
                "Hardware Version: {}, "
                "Firmware Version: {}".format(
                    hw_type, hw_version, fw_version
                ))

            self.sensor.set_gain(float(self.gain))
            self.sensor.set_indicator_led_current(float(self.indicator_led_current))
            self.sensor.set_illumination_led_current(float(self.illumination_led_current))
            self.sensor.set_integration_time(self.integration_time)

    def get_measurement(self):
        """ Gets the DS18B20's temperature in Celsius """
        self.return_dict = measurements_dict.copy()

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

            if self.is_enabled(index):
                self.value_set(index, color_value)

        return self.return_dict

    def stop_input(self):
        """ Called when Input is deactivated """
        self.sensor.set_measurement_mode(3)
        self.sensor.set_indicator_led(0)
        self.sensor.set_illumination_led(0)
        self.running = False
        try:
            if self.lock_file:
                self.lock_release(self.lock_file)
        except:
            pass
