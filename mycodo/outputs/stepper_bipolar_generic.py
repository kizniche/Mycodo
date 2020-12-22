# coding=utf-8
#
# stepper_ drv8825.py - Output for DRV-8825 stepper controller
#
import copy
import time

from flask_babel import lazy_gettext

from mycodo.outputs.base_output import AbstractOutput
from mycodo.utils.influx import add_measurements_influxdb


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


def constraints_pass_positive_or_zero_value(mod_input, value):
    """
    Check if the user input is acceptable
    :param mod_input: SQL object with user-saved Input options
    :param value: float or int
    :return: tuple: (bool, list of strings)
    """
    errors = []
    all_passed = True
    # Ensure value is positive
    if value < 0:
        all_passed = False
        errors.append("Must be zero or a positive value")
    return all_passed, errors, mod_input


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
    'output_name': "{}: {}, {}".format(
        lazy_gettext('Stepper Motor'),
        lazy_gettext('Bipolar'),
        lazy_gettext('Generic')),
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
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO')
    ],

    'interfaces': ['GPIO'],

    'custom_options': [
        {
            'type': 'message',
            'default_value': 'If the Direction or Enable pins are not used, make sure you pull the appropriate pins on your driver high or low to set the proper direction and enable the stepper motor to be energized. Note: For Enable Mode, always having the motor energized will use more energy and produce more heat.',
        },
        {
            'id': 'pin_step',
            'type': 'integer',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_value,
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
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Direction Pin',
            'phrase': 'The Direction pin of the controller (BCM numbering). 0 to disable.'
        },
        {
            'id': 'pin_enable',
            'type': 'integer',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Enable Pin',
            'phrase': 'The Enable pin of the controller (BCM numbering). 0 to disable.'
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
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Mode Pin 1',
            'phrase': 'The Mode Pin 1 of the controller (BCM numbering). 0 to disable.'
        },
        {
            'id': 'pin_mode_2',
            'type': 'integer',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Mode Pin 2',
            'phrase': 'The Mode Pin 2 of the controller (BCM numbering). 0 to disable.'
        },
        {
            'id': 'pin_mode_3',
            'type': 'integer',
            'default_value': 0,
            'constraints_pass': constraints_pass_positive_or_zero_value,
            'name': 'Mode Pin 3',
            'phrase': 'The Mode Pin 3 of the controller (BCM numbering). 0 to disable.'
        }
    ]
}


class OutputModule(AbstractOutput):
    """
    An output support class that operates an output
    """
    def __init__(self, output, testing=False):
        super(OutputModule, self).__init__(output, testing=testing, name=__name__)

        self.stepper = None
        self.output_setup = False
        self.stepper_running = None

        self.pin_enable = None
        self.enable_mode = None
        self.enable_shutdown = None
        self.pin_step = None
        self.pin_dir = None
        self.pin_mode_1 = None
        self.pin_mode_2 = None
        self.pin_mode_3 = None
        self.full_step_delay = None
        self.step_resolution = None

        self.setup_custom_options(
            OUTPUT_INFORMATION['custom_options'], output)

    def setup_output(self):
        self.setup_on_off_output(OUTPUT_INFORMATION)

        mode_pins = []
        if self.pin_mode_1 and self.pin_mode_2 and self.pin_mode_3:
            mode_pins = (self.pin_mode_1, self.pin_mode_2, self.pin_mode_3)
        elif any([self.pin_mode_1, self.pin_mode_2, self.pin_mode_3]):
            self.logger.warning(
                "When setting mode pins, this driver needs all three to be set.")
        elif self.step_resolution != "Full":
            self.logger.warning(
                "When using a step resolution other than Full, mode pins should be set. "
                "Only proceed if you know what you're doing (e.g. they're pulled high/low "
                "on the board and not via Mycodo GPIO pins).")

        if self.pin_step:
            try:
                self.stepper = StepperMotor(
                    self.pin_enable,
                    self.pin_step,
                    self.pin_dir,
                    mode_pins,
                    self.step_resolution,
                    self.full_step_delay)
                self.stepper_running = False
                self.output_setup = True

                if self.pin_enable and self.enable_mode == "always":
                    self.stepper.enable(True)
            except:
                self.logger.exception("Stepper setup")
                self.output_setup = False
        else:
            self.logger.error("Step pin must be set")

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        measure_dict = copy.deepcopy(measurements_dict)

        if amount not in [None, 0]:
            if amount > 0:
                self.stepper_running = True
                if self.pin_enable and self.enable_mode == "only_run":
                    self.stepper.enable(True)
                self.stepper.run(int(amount), True)
                if self.pin_enable and self.enable_mode == "only_run":
                    self.stepper.enable(False)
                self.stepper_running = False
            else:
                self.stepper_running = True
                if self.pin_enable and self.enable_mode == "only_run":
                    self.stepper.enable(True)
                self.stepper.run(int(abs(amount)), False)
                if self.pin_enable and self.enable_mode == "only_run":
                    self.stepper.enable(False)
                self.stepper_running = False
            measure_dict[0]['value'] = amount
        elif state == "off":
            if self.pin_enable and self.enable_mode == "only_run":
                self.stepper.enable(False)
            self.stepper_running = False
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
            return self.stepper_running

    def is_setup(self):
        if self.output_setup:
            return True
        return False

    def stop_output(self):
        """ Called when Output is stopped """
        if self.pin_enable:
            if self.enable_shutdown == "enable":
                self.stepper.enable(True)
            elif self.enable_shutdown == "disable":
                self.stepper.enable(False)
        self.running = False


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

    def run(self, steps, clockwise):
        if self.dir_pin:
            self.GPIO.output(self.dir_pin, clockwise)
        for _ in range(steps):
            self.GPIO.output(self.step_pin, self.GPIO.HIGH)
            time.sleep(self.delay)
            self.GPIO.output(self.step_pin, self.GPIO.LOW)
            time.sleep(self.delay)
