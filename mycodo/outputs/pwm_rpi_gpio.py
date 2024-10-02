# coding=utf-8
#
# pwm_rpi_gpio.py - Output for GPIO PWM using RPi.GPIO
#
import copy

from flask_babel import lazy_gettext
from sqlalchemy import and_

from mycodo.databases.models import DeviceMeasurements, OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import (
    constraints_pass_positive_or_zero_value, constraints_pass_positive_value)
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb, read_influxdb_single
from mycodo.utils.system_pi import return_measurement_info

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
    'output_name_unique': 'pwm_rpi_gpio',
    'output_name': "{}: Raspberry Pi GPIO (Pi <= 4)".format(lazy_gettext('PWM')),
    'output_library': 'RPi.GPIO',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['pwm'],

    'message': 'A software implementation of PWM using the RPi.GPIO library.',

    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO==0.7.1'),
    ],

    'interfaces': ['GPIO'],

    'custom_commands': [
        {
            'type': 'message',
            'default_value': """Set the Duty Cycle."""
        },
        {
            'id': 'duty_cycle',
            'type': 'float',
            'default_value': 0,
            'name': 'Duty Cycle',
            'phrase': 'The duty cycle to set'
        },
        {
            'id': 'set_duty_cycle',
            'type': 'button',
            'wait_for_return': True,
            'name': 'Set Duty Cycle'
        }
    ],

    'custom_channel_options': [
        {
            'id': 'pin',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': "{}: {} ({})".format(lazy_gettext('Pin'), lazy_gettext('GPIO'), lazy_gettext('BCM')),
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
            'phrase': 'Set the state when Mycodo starts'
        },
        {
            'id': 'startup_value',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Startup Value'),
            'phrase': 'The value when Mycodo starts'
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
            'phrase': 'Set the state when Mycodo shuts down'
        },
        {
            'id': 'shutdown_value',
            'type': 'float',
            'default_value': 0.0,
            'required': True,
            'name': lazy_gettext('Shutdown Value'),
            'phrase': 'The value when Mycodo shuts down'
        },
        {
            'id': 'pwm_hertz',
            'type': 'integer',
            'default_value': 1000,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': lazy_gettext('Frequency (Hertz)'),
            'phrase': 'The Hertz to output the PWM signal'
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

        self.duty_cycle = None
        self.pwm_output = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        from RPi import GPIO

        GPIO.setmode(GPIO.BCM)

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
            GPIO.setup(self.options_channels['pin'][0], GPIO.OUT)
            self.pwm_output = GPIO.PWM(self.options_channels['pin'][0], self.options_channels['pwm_hertz'][0])
            self.pwm_output.start(0)
            self.duty_cycle = 0

            self.logger.info("Output setup on pin {pin} at {hz} Hz".format(
                pin=self.options_channels['pin'][0],
                hz=self.options_channels['pwm_hertz'][0]))

            self.output_setup = True

            if self.options_channels['state_startup'][0] == 0:
                self.output_switch('off')
                self.logger.info("PWM turned off (0 % duty cycle)")
            elif self.options_channels['state_startup'][0] == 'set_duty_cycle':
                self.output_switch('on', amount=self.options_channels['startup_value'][0])
                self.logger.info("PWM set to {} % duty cycle (user-specified value)".format(
                    self.options_channels['startup_value'][0]))
            elif self.options_channels['state_startup'][0] == 'last_duty_cycle':
                device_measurement = db_retrieve_table_daemon(DeviceMeasurements).filter(
                    and_(DeviceMeasurements.device_id == self.unique_id,
                         DeviceMeasurements.channel == 0)).first()

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
                    self.logger.info(
                        "PWM set to {} % duty cycle (last known value)".format(
                            last_measurement[1]))
                    self.output_switch('on', amount=last_measurement[1])
                else:
                    self.logger.error(
                        "Output instructed at startup to be set to "
                        "the last known duty cycle, but a last known "
                        "duty cycle could not be found in the measurement "
                        "database")
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

        self.pwm_output.ChangeDutyCycle(amount)
        self.duty_cycle = amount

        self.logger.debug("Duty cycle set to {dc:.2f} %".format(dc=amount))

        if self.options_channels['pwm_invert_stored_signal'][0]:
            amount = 100.0 - abs(amount)

        measure_dict[0]['value'] = float(amount)
        add_measurements_influxdb(self.unique_id, measure_dict)

        return "success"

    def is_on(self, output_channel=None):
        if self.is_setup():
            if self.duty_cycle > 0:
                return self.duty_cycle

            return False

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            if self.options_channels['state_shutdown'][0] == 0:
                self.output_switch('off')
            elif self.options_channels['state_shutdown'][0] == 'set_duty_cycle':
                self.output_switch('on', amount=self.options_channels['shutdown_value'][0])
        self.running = False

    def set_duty_cycle(self, args_dict):
        if 'duty_cycle' not in args_dict:
            self.logger.error("Cannot set without duty cycle")
            return
        return_str = self.control.output_on(
            self.output.unique_id,
            output_type='pwm',
            amount=args_dict["duty_cycle"],
            output_channel=0)
        return f"Setting duty cycle: {return_str}"
