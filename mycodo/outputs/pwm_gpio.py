# coding=utf-8
#
# pwm_gpio.py - Output for GPIO PWM
#
import copy

from flask_babel import lazy_gettext
from sqlalchemy import and_

from mycodo.databases.models import DeviceMeasurements
from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb
from mycodo.utils.influx import read_last_influxdb
from mycodo.utils.system_pi import return_measurement_info


def constraints_pass_positive_value(mod_dev, value):
    """
    Check if the user input is acceptable
    :param mod_dev: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value <= 0:
        all_passed = False
        errors.append("Must be a positive value")
    return all_passed, errors, mod_dev


# Measurements
measurements_dict = {
    0: {
        'measurement': 'duty_cycle',
        'unit': 'percent'
    }
}

channels_dict = {
    0: {
        'types': ['pwm'],
        'measurements': [0]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'pwm',
    'output_name': "GPIO: {}".format(lazy_gettext('PWM')),
    'output_library': 'pigpio',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['pwm'],

    'message': 'See the PWM section of the manual for PWM information and determining which '
               'pins may be used for each library option.',

    'options_enabled': [
        'button_send_duty_cycle'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('internal', 'file-exists /opt/mycodo/pigpio_installed', 'pigpio')
    ],

    'interfaces': ['GPIO'],

    'custom_channel_options': [
        {
            'id': 'pin',
            'type': 'integer',
            'default_value': None,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('GPIO Pin (BCM)'),
            'phrase': lazy_gettext('The pin to control the state of')
        },
        {
            'id': 'state_startup',
            'type': 'select',
            'default_value': '',
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                ('set_duty_cycle', 'User Set Value'),
                ('last_duty_cycle', 'Last Known Value')
            ],
            'name': lazy_gettext('Startup State'),
            'phrase': lazy_gettext('Set the state when Mycodo starts')
        },
        {
            'id': 'startup_value',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Startup Value'),
            'phrase': lazy_gettext('The value when Mycodo starts')
        },
        {
            'id': 'state_shutdown',
            'type': 'select',
            'default_value': '',
            'options_select': [
                (-1, 'Do Nothing'),
                (0, 'Off'),
                ('set_duty_cycle', 'User Set Value')
            ],
            'name': lazy_gettext('Shutdown State'),
            'phrase': lazy_gettext('Set the state when Mycodo shuts down')
        },
        {
            'id': 'shutdown_value',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Shutdown Value'),
            'phrase': lazy_gettext('The value when Mycodo shuts down')
        },
        {
            'id': 'pwm_library',
            'type': 'select',
            'default_value': 'pigpio_any',
            'options_select': [
                ('pigpio_any', 'Any Pin, <= 40 kHz'),
                ('pigpio_hardware', 'Hardware Pin, <= 30 MHz')
            ],
            'name': lazy_gettext('Library'),
            'phrase': lazy_gettext('Which method to produce the PWM signal (hardware pins can produce higher frequencies)')
        },
        {
            'id': 'pwm_hertz',
            'type': 'integer',
            'default_value': 22000,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Frequency (Hertz)'),
            'phrase': lazy_gettext('The Herts to output the PWM signal (0 - 70,000)')
        },
        {
            'id': 'pwm_invert_signal',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Invert Signal'),
            'phrase': lazy_gettext('Invert the PWM signal')
        },
        {
            'id': 'trigger_functions_startup',
            'type': 'bool',
            'default_value': False,
            'name': lazy_gettext('Trigger Functions at Startup'),
            'phrase': lazy_gettext('Whether to trigger functions when the output switches at startup')
        },
        {
            'id': 'amps',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Current (Amps)'),
            'phrase': lazy_gettext('The current draw of the device being controlled')
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.pigpio = None
        self.pwm_output = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def setup_output(self):
        import pigpio

        self.pigpio = pigpio

        self.setup_output_variables(OUTPUT_INFORMATION)

        error = []
        if self.options_channels['pin'][0] is None:
            error.append("Pin must be set")
        if self.options_channels['pwm_hertz'][0] <= 0:
            error.append("PWM Hertz must be a positive value")
        if error:
            for each_error in error:
                self.logger.error(each_error)
            return

        try:
            self.pwm_output = self.pigpio.pi()
            if not self.pwm_output.connected:
                self.logger.error("Could not connect to pigpiod")
                self.pwm_output = None
                return
            if self.options_channels['pwm_library'][0] == 'pigpio_hardware':
                self.pwm_output.hardware_PWM(
                    self.options_channels['pin'][0], self.options_channels['pwm_hertz'][0], 0)
            elif self.options_channels['pwm_library'][0] == 'pigpio_any':
                self.pwm_output.set_PWM_frequency(
                    self.options_channels['pin'][0], self.options_channels['pwm_hertz'][0])

            self.output_setup = True

            state_string = ""
            if self.options_channels['state_startup'][0] == 0:
                self.output_switch('off')
                state_string += " and turned off (0 % duty cycle)"
            elif self.options_channels['state_startup'][0] == 'set_duty_cycle':
                self.output_switch('on', amount=self.options_channels['startup_value'][0])
                state_string += " and {} % duty cycle (user-specified value)".format(self.options_channels['startup_value'][0])
            elif self.options_channels['state_startup'][0] == 'last_duty_cycle':
                device_measurement = db_retrieve_table_daemon(DeviceMeasurements).filter(
                    and_(DeviceMeasurements.device_id == self.unique_id,
                         DeviceMeasurements.channel == 0)).first()

                last_measurement = None
                if device_measurement:
                    channel, unit, measurement = return_measurement_info(device_measurement, None)
                    last_measurement = read_last_influxdb(
                        self.unique_id,
                        unit,
                        channel,
                        measure=measurement,
                        duration_sec=None)

                if last_measurement:
                    state_string += " and {} % duty cycle (last known value)".format(last_measurement[1])
                    self.output_switch('on', amount=last_measurement[1])
                else:
                    self.logger.error(
                        "Output instructed at startup to be set to "
                        "the last known duty cycle, but a last known "
                        "duty cycle could not be found in the measurement "
                        "database")

            self.logger.info("Output setup on pin {pin} at {hz} Hertz{ss}".format(
                pin=self.options_channels['pin'][0],
                hz=self.options_channels['pwm_hertz'][0],
                ss=state_string))
        except Exception as except_msg:
            self.logger.exception("Output was unable to be setup on pin {pin}: {err}".format(
                pin=self.options_channels['pin'][0], err=except_msg))

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        measure_dict = copy.deepcopy(measurements_dict)

        if state == 'on':
            if self.options_channels['pwm_invert_signal'][0]:
                amount = 100.0 - abs(amount)
        elif state == 'off':
            if self.options_channels['pwm_invert_signal'][0]:
                amount = 100
            else:
                amount = 0

        if self.options_channels['pwm_library'][0] == 'pigpio_hardware':
            self.pwm_output.hardware_PWM(
                self.options_channels['pin'][0],
                self.options_channels['pwm_hertz'][0],
                int(amount * 10000))
        elif self.options_channels['pwm_library'][0] == 'pigpio_any':
            self.pwm_output.set_PWM_frequency(
                self.options_channels['pin'][0], self.options_channels['pwm_hertz'][0])
            self.pwm_output.set_PWM_range(self.options_channels['pin'][0], 1000)
            self.pwm_output.set_PWM_dutycycle(
                self.options_channels['pin'][0], self.duty_cycle_to_pigpio_value(amount))

        measure_dict[0]['value'] = amount
        add_measurements_influxdb(self.unique_id, measure_dict)

        self.logger.debug("Duty cycle set to {dc:.2f} %".format(dc=amount))
        return "success"

    def is_on(self, output_channel=None):
        if self.is_setup():
            response = self.pwm_output.get_PWM_dutycycle(self.options_channels['pin'][0])
            if self.options_channels['pwm_library'][0] == 'pigpio_hardware':
                duty_cycle = response / 10000
            elif self.options_channels['pwm_library'][0] == 'pigpio_any':
                duty_cycle = self.pigpio_value_to_duty_cycle(response)
            else:
                return None

            if duty_cycle > 0:
                return duty_cycle

            return False

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """ Called when Output is stopped """
        if self.options_channels['state_shutdown'][0] == 0:
            self.output_switch('off')
        elif self.options_channels['state_shutdown'][0] == 'set_duty_cycle':
            self.output_switch('on', amount=self.options_channels['shutdown_value'][0])
        self.running = False

    @staticmethod
    def duty_cycle_to_pigpio_value(duty_cycle):
        pigpio_value = int((abs(duty_cycle) / 100.0) * 1000)
        if pigpio_value > 1000:
            pigpio_value = 1000
        elif pigpio_value < 0:
            pigpio_value = 0
        return pigpio_value

    @staticmethod
    def pigpio_value_to_duty_cycle(pigpio_value):
        duty_cycle = (abs(pigpio_value) / 1000.0) * 100
        if duty_cycle > 100:
            duty_cycle = 100
        elif duty_cycle < 0:
            duty_cycle = 0
        return duty_cycle
