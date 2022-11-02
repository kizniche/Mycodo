# coding=utf-8
#
# motor_stepper_bipolar_generaic.py - Output for stepper motor
#
import copy
import time

from flask_babel import lazy_gettext

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.constraints_pass import constraints_pass_positive_or_zero_value
from mycodo.utils.constraints_pass import constraints_pass_positive_value
from mycodo.utils.database import db_retrieve_table_daemon
from mycodo.utils.influx import add_measurements_influxdb

# Measurements
measurements_dict = {
    0: {
        'measurement': 'rotation',
        'unit': 'steps'
    }
}

channels_dict = {
    0: {
        'types': ['value'],
        'measurements': [0]
    }
}

# Output information
OUTPUT_INFORMATION = {
    'output_name_unique': 'stepper_bipolar_generic',
    'output_name': "{}: {}, {} ({})".format(lazy_gettext('Motor'), lazy_gettext('Stepper Motor'), lazy_gettext('Bipolar'), lazy_gettext('Generic')),
    'output_library': 'RPi.GPIO',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['value'],

    'url_manufacturer': [
        'https://www.ti.com/product/DRV8825',
        'https://www.allegromicro.com/en/products/motor-drivers/brush-dc-motor-drivers/a4988'],
    'url_datasheet': [
        'https://www.ti.com/lit/ds/symlink/drv8825.pdf',
        'https://www.allegromicro.com/-/media/files/datasheets/a4988-datasheet.ashx'],
    'url_product_purchase': [
        'https://www.pololu.com/product/2133',
        'https://www.pololu.com/product/1182'],

    'message': 'This is a generic module for bipolar stepper motor drivers such as the '
               'DRV8825, A4988, and others. The value passed to the output is the number '
               'of steps. A positive value turns clockwise and a negative value turns '
               'counter-clockwise.',

    'options_enabled': [
        'button_send_value'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO==0.7.1')
    ],

    'interfaces': ['GPIO'],

    'custom_channel_options': [
        {
            'type': 'message',
            'default_value': 'If the Direction or Enable pins are not used, make sure you pull the appropriate pins on your driver high or low to set the proper direction and enable the stepper motor to be energized. Note: For Enable Mode, always having the motor energized will use more energy and produce more heat.',
        },
        {
            'id': 'pin_step',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Step Pin',
            'phrase': 'The Step pin of the controller (BCM numbering)'
        },
        {
            'id': 'full_step_delay',
            'type': 'float',
            'default_value': 0.005,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Full Step Delay',
            'phrase': 'The Full Step Delay of the controller'
        },
        {
            'id': 'pin_dir',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Direction Pin',
            'phrase': "{} {}".format(
                'The Direction pin of the controller (BCM numbering).',
                lazy_gettext('Set to None to disable.'))
        },
        {
            'id': 'pin_enable',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Enable Pin',
            'phrase': 'The Enable pin of the controller (BCM numbering). {}'.format(
                lazy_gettext('Set to None to disable.'))
        },
        {
            'id': 'enable_mode',
            'type': 'select',
            'default_value': 'only_run',
            'options_select': [
                ('only_run', 'Only When Turning'),
                ('always', 'Always'),
            ],
            'name': 'Enable Mode',
            'phrase': 'Choose when to pull the enable pin high to energize the motor.'
        },
        {
            'id': 'enable_shutdown',
            'type': 'select',
            'default_value': 'disable',
            'options_select': [
                ('enable', 'Enable'),
                ('disable', 'Disable'),
            ],
            'name': 'Enable at Shutdown',
            'phrase': 'Choose whether the enable pin in pulled high (Enable) or low (Disable) when Mycodo shuts down.'
        },
        {'type': 'new_line'},
        {
            'type': 'message',
            'default_value': 'If using a Step Resolution other than Full, and all three Mode Pins are set, they will be set high (1) or how (0) according to the values in parentheses to the right of the selected Step Resolution, e.g. (Mode Pin 1, Mode Pin 2, Mode Pin 3).',
        },
        {
            'id': 'step_resolution',
            'type': 'select',
            'default_value': 'Full',
            'options_select': [
                ('Full', 'Full (modes 0, 0, 0)'),
                ('Half', 'Half (modes 1, 0, 0)'),
                ('1/4', '1/4 (modes 0, 1, 0)'),
                ('1/8', '1/8 (modes 1, 1, 0)'),
                ('1/16', '1/16 (modes 0, 0, 1)'),
                ('1/32', '1/32 (modes 1, 0, 1)')
            ],
            'name': 'Step Resolution',
            'phrase': 'The Step Resolution of the controller'
        },
        {
            'id': 'pin_mode_1',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Mode Pin 1',
            'phrase': 'The Mode Pin 1 of the controller (BCM numbering). {}'.format(
                lazy_gettext('Set to None to disable.'))
        },
        {
            'id': 'pin_mode_2',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Mode Pin 2',
            'phrase': 'The Mode Pin 2 of the controller (BCM numbering). {}'.format(
                lazy_gettext('Set to None to disable.'))
        },
        {
            'id': 'pin_mode_3',
            'type': 'integer',
            'default_value': None,
            'required': False,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Mode Pin 3',
            'phrase': 'The Mode Pin 3 of the controller (BCM numbering). {}'.format(
                lazy_gettext('Set to None to disable.'))
        }
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.stepper = None

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        self.setup_output_variables(OUTPUT_INFORMATION)

        mode_pins = []
        if (self.options_channels['pin_mode_1'][0] and
                self.options_channels['pin_mode_2'][0] and
                self.options_channels['pin_mode_3'][0]):
            mode_pins = (self.options_channels['pin_mode_1'][0],
                         self.options_channels['pin_mode_2'][0],
                         self.options_channels['pin_mode_3'][0])
        elif any([self.options_channels['pin_mode_1'][0],
                  self.options_channels['pin_mode_2'][0],
                  self.options_channels['pin_mode_3'][0]]):
            self.logger.warning(
                "When setting mode pins, this driver needs all three to be set.")
        elif self.options_channels['step_resolution'][0] != "Full":
            self.logger.warning(
                "When using a step resolution other than Full, mode pins should be set. "
                "Only proceed if you know what you're doing (e.g. they're pulled high/low "
                "on the board and not via Mycodo GPIO pins).")

        if self.options_channels['pin_step'][0]:
            try:
                self.stepper = StepperMotor(
                    self.options_channels['pin_enable'][0],
                    self.options_channels['pin_step'][0],
                    self.options_channels['pin_dir'][0],
                    mode_pins,
                    self.options_channels['step_resolution'][0],
                    self.options_channels['full_step_delay'][0])
                self.output_setup = True

                if (self.options_channels['pin_enable'][0] and
                        self.options_channels['enable_mode'][0] == "always"):
                    self.stepper.enable(True)
            except:
                self.logger.exception("Stepper setup")
                self.output_setup = False
        else:
            self.logger.error("Step pin must be set")

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        measure_dict = copy.deepcopy(measurements_dict)

        if amount not in [None, 0]:
            if (self.options_channels['pin_enable'][0] and
                    self.options_channels['enable_mode'][0] == "only_run"):
                self.stepper.enable(True)
                
            if amount > 0:
                self.stepper.run(int(amount), True)
            elif amount < 0:
                self.stepper.run(int(abs(amount)), False)
            
            if (self.options_channels['pin_enable'][0] and
                    self.options_channels['enable_mode'][0] == "only_run"):
                self.stepper.enable(False)

            measure_dict[0]['value'] = amount
        elif state == "off":
            if (self.options_channels['pin_enable'][0] and
                    self.options_channels['enable_mode'][0] == "only_run"):
                self.stepper.enable(False)
            if self.stepper.running:
                self.stepper.stop_running()
        else:
            self.logger.error(
                "Invalid parameters: State: {state}, Type: {ot}, Amount: {amt}".format(
                    state=state,
                    ot=output_type,
                    amt=amount))
            return

        add_measurements_influxdb(self.unique_id, measure_dict)

    def is_on(self, output_channel=None):
        if self.is_setup():
            return self.stepper.running

    def is_setup(self):
        return self.output_setup

    def stop_output(self):
        """Called when Output is stopped."""
        if self.is_setup():
            if self.options_channels['enable_shutdown'][0] == "enable":
                self.stepper.enable(True)
            elif self.options_channels['enable_shutdown'][0] == "disable":
                self.stepper.enable(False)
        self.stepper.stop_running()


class StepperMotor:
    """
    Generic stepper motor driver
    Modified from https://github.com/dimschlukas/rpi_python_drv8825
    """
    def __init__(self, enable_pin, step_pin, dir_pin, mode_pins, step_type, full_step_delay):
        import RPi.GPIO as GPIO

        self.GPIO = GPIO

        self.enable_pin = enable_pin
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.break_turn = False
        self.running = False

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(step_pin, GPIO.OUT)

        if enable_pin:
            GPIO.setup(enable_pin, GPIO.OUT)
        if dir_pin:
            GPIO.setup(dir_pin, GPIO.OUT)
        if mode_pins and all(mode_pins):
            GPIO.setup(mode_pins, GPIO.OUT)

        resolution = {
            'Full': (0, 0, 0),
            'Half': (1, 0, 0),
            '1/4': (0, 1, 0),
            '1/8': (1, 1, 0),
            '1/16': (0, 0, 1),
            '1/32': (1, 0, 1)
        }
        micro_steps =  {
            'Full': 1,
            'Half': 2,
            '1/4': 4,
            '1/8': 8,
            '1/16': 16,
            '1/32': 32
        }

        self.delay = full_step_delay / micro_steps[step_type]
        if mode_pins and all(mode_pins):
            GPIO.output(mode_pins, resolution[step_type])

    def enable(self, enable):
        if self.enable_pin:
            self.GPIO.output(self.enable_pin, not enable)

    def stop_running(self):
        if self.running:
            self.break_turn = True

    def run(self, steps, clockwise):
        if self.dir_pin:
            self.GPIO.output(self.dir_pin, clockwise)
        self.running = True
        for _ in range(steps):
            if self.break_turn:
                break
            self.GPIO.output(self.step_pin, self.GPIO.HIGH)
            time.sleep(self.delay)
            self.GPIO.output(self.step_pin, self.GPIO.LOW)
            time.sleep(self.delay)
        self.running = False
        self.break_turn = False
