# coding=utf-8
#
# pwm_pca9685.py - Output for PCA9685
#
import copy

from flask_babel import lazy_gettext
from sqlalchemy import and_

from mycodo.config_translations import TRANSLATIONS
from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_percent
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_influxdb_single
from mycodo.utils.system_pi import return_measurement_info


def constraints_pass_hertz(mod_dev, value):
    """
    Check if the user input is acceptable
    :param mod_dev: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    if value < 40 or value > 1600:
        all_passed = False
        errors.append("Must be a value between 40 and 1600")
    return all_passed, errors, mod_dev


# Measurements
measurements_dict = {
    key: {
        'measurement': 'duty_cycle',
        'unit': 'percent'
    }
    for key in range(16)
}

channels_dict = {
    key: {
        'name': f'Channel {key + 1}',
        'types': ['pwm'],
        'measurements': [key]
    }
    for key in range(16)
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'pwm_pca9685',
    'output_name': "{}: PCA9685 16-Channel {}".format(lazy_gettext('PWM'), lazy_gettext('LED Controller')),
    'output_manufacturer': 'NXP Semiconductors',
    'output_library': 'adafruit-pca9685',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['pwm'],

    'url_manufacturer': 'https://www.nxp.com/products/power-management/lighting-driver-and-controller-ics/ic-led-controllers/16-channel-12-bit-pwm-fm-plus-ic-bus-led-controller:PCA9685',
    'url_datasheet': 'https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf',
    'url_product_purchase': 'https://www.adafruit.com/product/815',

    'message': 'The PCA9685 can output a PWM signal to 16 channels at a frequency between 40 and 1600 Hz.',

    'options_enabled': [
        'i2c_location',
        'button_send_duty_cycle'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'Adafruit_PCA9685', 'adafruit-pca9685==1.0.1')
    ],

    'interfaces': ['I2C'],
    'i2c_location': [
        '0x40', '0x41', '0x42', '0x43', '0x44', '0x45', '0x46', '0x47',
        '0x48', '0x49', '0x4a', '0x4b', '0x4c', '0x4d', '0x4e', '0x4f',
        '0x50', '0x51', '0x52', '0x53', '0x54', '0x55', '0x56', '0x57',
        '0x58', '0x59', '0x5a', '0x5b', '0x5c', '0x5d', '0x5e', '0x5f',
        '0x60', '0x61', '0x62', '0x63', '0x64', '0x65', '0x66', '0x67',
        '0x68', '0x69', '0x6a', '0x6b', '0x6c', '0x6d', '0x6e', '0x6f',
        '0x70', '0x71', '0x72', '0x73', '0x74', '0x75', '0x76', '0x77',
        '0x78', '0x79', '0x7a', '0x7b', '0x7c', '0x7d', '0x7e', '0x7f'
    ],
    'i2c_address_editable': False,
    'i2c_address_default': '0x40',

    'custom_options': [
        {
            'id': 'pwm_hertz',
            'type': 'integer',
            'default_value': 1600,
            'required': True,
            'constraints_pass': constraints_pass_hertz,
            'name': lazy_gettext('Frequency (Hertz)'),
            'phrase': 'The Herts to output the PWM signal (40 - 1600)'
        },
    ],

    'custom_channel_options': [
        {
            'id': 'name',
            'type': 'text',
            'default_value': '',
            'required': False,
            'name': TRANSLATIONS['name']['title'],
            'phrase': TRANSLATIONS['name']['phrase']
        },
        {
            'id': 'state_startup',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (0, 'Off'),
                ('set_duty_cycle', 'User Set Value'),
                ('last_duty_cycle', 'Last Known Value')
            ],
            'name': lazy_gettext('Startup State'),
            'phrase': 'Set the state when Mycodo starts'
        },
        {
            'id': 'startup_value',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_percent,
            'name': lazy_gettext('Startup Value'),
            'phrase': 'The value when Mycodo starts'
        },
        {
            'id': 'state_shutdown',
            'type': 'select',
            'default_value': 0,
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                ('set_duty_cycle', 'User Set Value')
            ],
            'name': lazy_gettext('Shutdown State'),
            'phrase': 'Set the state when Mycodo shuts down'
        },
        {
            'id': 'shutdown_value',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'constraints_pass': constraints_pass_percent,
            'name': lazy_gettext('Shutdown Value'),
            'phrase': 'The value when Mycodo shuts down'
        },
        {
            'id': 'pwm_invert_signal',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Invert Signal'),
            'phrase': 'Invert the PWM signal'
        },
        {
            'id': 'pwm_invert_stored_signal',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Invert Stored Signal'),
            'phrase': 'Invert the value that is saved to the measurement database'
        },
        {
            'id': 'amps',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': "{} ({})".format(lazy_gettext('Current'), lazy_gettext('Amps')),
            'phrase': 'The current draw of the device being controlled'
        }
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.pwm_duty_cycles = {}
        for i in range(16):
            self.pwm_duty_cycles[i] = 0
        self.pwm_output = None
        self.pwm_hertz = None

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        import Adafruit_PCA9685

        self.setup_output_variables(OUTPUT_INFORMATION)

        try:
            self.pwm_output = Adafruit_PCA9685.PCA9685(
                address=int(str(self.output.i2c_location), 16),
                busnum=self.output.i2c_bus)
 
            self.pwm_output.set_pwm_freq(self.pwm_hertz)

            self.output_setup = True
            self.logger.debug("Output setup on bus {} at {}".format(
                self.output.i2c_bus, self.output.i2c_location))

            for i in range(16):
                if self.options_channels['state_startup'][i] == 0:
                    self.logger.debug("Startup state channel {ch}: off".format(ch=i))
                    self.output_switch('off', output_channel=i)
                elif self.options_channels['state_startup'][i] == 'set_duty_cycle':
                    self.logger.debug("Startup state channel {ch}: on ({dc:.2f} %)".format(
                        ch=i, dc=self.options_channels['startup_value'][i]))
                    self.output_switch('on', output_channel=i, amount=self.options_channels['startup_value'][i])
                elif self.options_channels['state_startup'][i] == 'last_duty_cycle':
                    self.logger.debug("Startup state channel {ch}: last".format(ch=i))
                    device_measurement = db_retrieve_table_daemon(DeviceMeasurements).filter(
                        and_(DeviceMeasurements.device_id == self.unique_id,
                             DeviceMeasurements.channel == i)).first()

                    last_measurement = None
                    if device_measurement:
                        channel, unit, measurement = return_measurement_info(device_measurement, None)
                        last_measurement = read_influxdb_single(
                            self.unique_id,
                            unit,
                            channel,
                            measure=measurement,
                            value='LAST')

                    if last_measurement:
                        self.logger.debug("Setting channel {ch} startup duty cycle to last known value of {dc} %".format(
                            ch=i, dc=last_measurement[1]))
                        self.output_switch('on', amount=last_measurement[1])
                    else:
                        self.logger.error(
                            "Output channel {} instructed at startup to be set to "
                            "the last known duty cycle, but a last known "
                            "duty cycle could not be found in the measurement "
                            "database".format(i))
                else:
                    self.logger.debug("Startup state channel {ch}: no change".format(ch=i))
        except Exception as except_msg:
            self.logger.exception("Output was unable to be setup: {err}".format(err=except_msg))

    def output_switch(self, state, output_type=None, amount=0, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        measure_dict = copy.deepcopy(measurements_dict)

        output_amount = 0

        if state == 'on':
            if self.options_channels['pwm_invert_signal'][output_channel]:
                output_amount = 100.0 - abs(amount)
            else:
                output_amount = abs(amount)
        elif state == 'off':
            if self.options_channels['pwm_invert_signal'][output_channel]:
                output_amount = 100
            else:
                output_amount = 0

        off_at_tick = round(output_amount * 4095. / 100.)
        self.pwm_output.set_pwm(output_channel, 0, off_at_tick)

        self.pwm_duty_cycles[output_channel] = amount

        self.logger.debug(
            "Duty cycle of channel {ch} set to {dc:.2f} % (switched off for {off_at_tick:d} of 4095 ticks)".format(
                ch=output_channel, dc=amount, off_at_tick=off_at_tick))

        if self.options_channels['pwm_invert_stored_signal'][output_channel]:
            amount = 100.0 - abs(amount)

        measure_dict[output_channel]['value'] = float(amount)
        add_measurements_influxdb(self.unique_id, measure_dict)

        return "success"

    def is_on(self, output_channel=None):
        if self.is_setup():
            duty_cycle = self.pwm_duty_cycles[output_channel]
            if duty_cycle:
                return duty_cycle

            return False

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            for i in range(16):
                if self.options_channels['state_shutdown'][i] == 0:
                    self.output_switch('off')
                elif self.options_channels['state_shutdown'][i] == 'set_duty_cycle':
                    self.output_switch('on', amount=self.options_channels['shutdown_value'][i])
        self.running = False
