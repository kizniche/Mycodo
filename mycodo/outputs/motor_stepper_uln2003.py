# coding=utf-8
#
# motor_stepper_uln2003.py - Output for ULN2003 stepper motor driver
#
import copy

from flask_babel import lazy_gettext

from mycodo.databases.models import OutputChannel
from mycodo.outputs.base_output import AbstractOutput
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
    'output_name_unique': 'stepper_uln2003',
    'output_name': "{}: ULN2003 {}, {}".format(lazy_gettext('Motor'), lazy_gettext('Stepper Motor'), lazy_gettext('Unipolar')),
    'output_manufacturer': 'STMicroelectronics',
    'output_library': 'RPi.GPIO, rpimotorlib',
    'measurements_dict': measurements_dict,
    'channels_dict': channels_dict,
    'output_types': ['value'],

    'url_manufacturer': [
        'https://www.ti.com/product/ULN2003A'
    ],
    'url_datasheet': [
        'https://www.electronicoscaldas.com/datasheet/ULN2003A-PCB.pdf',
        'https://www.ti.com/lit/ds/symlink/uln2003a.pdf?ts=1617254568263&ref_url=https%253A%252F%252Fwww.ti.com%252Fproduct%252FULN2003A'
    ],

    'message': 'This is a module for the ULN2003 driver.',

    'options_enabled': [
        'button_send_value'
    ],
    'options_disabled': ['interface'],

    'dependencies_module': [
        ('pip-pypi', 'RPi.GPIO', 'RPi.GPIO==0.7.1'),
        ('pip-pypi', 'RpiMotorLib', 'rpimotorlib==2.7')
    ],

    'interfaces': ['GPIO'],

    'custom_channel_options': [
        {
            'type': 'message',
            'default_value': 'Notes about connecting the ULN2003...',
        },
        {
            'id': 'pin_in1',
            'type': 'integer',
            'default_value': 18,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Pin IN1',
            'phrase': 'The pin (BCM numbering) connected to IN1 of the ULN2003'
        },
        {
            'id': 'pin_in2',
            'type': 'integer',
            'default_value': 23,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Pin IN2',
            'phrase': 'The pin (BCM numbering) connected to IN2 of the ULN2003'
        },
        {
            'id': 'pin_in3',
            'type': 'integer',
            'default_value': 24,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Pin IN3',
            'phrase': 'The pin (BCM numbering) connected to IN3 of the ULN2003'
        },
        {
            'id': 'pin_in4',
            'type': 'integer',
            'default_value': 25,
            'required': True,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Pin IN4',
            'phrase': 'The pin (BCM numbering) connected to IN4 of the ULN2003'
        },
        {
            'id': 'step_delay',
            'type': 'float',
            'default_value': 0.001,
            'constraints_pass': constraints_pass_positive_value,
            'name': 'Step Delay',
            'phrase': 'The Step Delay of the controller'
        },
        {'type': 'new_line'},
        {
            'type': 'message',
            'default_value': 'Notes about step resolution...',
        },
        {
            'id': 'step_resolution',
            'type': 'select',
            'default_value': 'full',
            'options_select': [
                ('full', 'Full'),
                ('half', 'Half'),
                ('wave', 'Wave')
            ],
            'name': 'Step Resolution',
            'phrase': 'The Step Resolution of the controller'
        }
    ]
}


class OutputModule(AbstractOutput):
    """An output support class that operates an output."""
    def __init__(self, output, testing=False):
        super().__init__(output, testing=testing, name=__name__)

        self.stepper = None
        self.stepper_running = False
        self.pins = []

        output_channels = db_retrieve_table_daemon(
            OutputChannel).filter(OutputChannel.output_id == self.output.unique_id).all()
        self.options_channels = self.setup_custom_channel_options_json(
            OUTPUT_INFORMATION['custom_channel_options'], output_channels)

    def initialize(self):
        from RpiMotorLib import RpiMotorLib

        self.setup_output_variables(OUTPUT_INFORMATION)

        try:
            if (self.options_channels['pin_in1'][0] and
                    self.options_channels['pin_in2'][0] and
                    self.options_channels['pin_in3'][0] and
                    self.options_channels['pin_in4'][0]):
                self.pins = [self.options_channels['pin_in1'][0],
                             self.options_channels['pin_in2'][0],
                             self.options_channels['pin_in3'][0],
                             self.options_channels['pin_in4'][0]]
                self.stepper = RpiMotorLib.BYJMotor("Motor", "28BYJ")
                self.output_setup = True
        except:
            self.logger.exception("Stepper setup")

    def output_switch(self, state, output_type=None, amount=None, output_channel=None):
        if not self.is_setup():
            msg = "Error 101: Device not set up. See https://kizniche.github.io/Mycodo/Error-Codes#error-101 for more info."
            self.logger.error(msg)
            return msg

        measure_dict = copy.deepcopy(measurements_dict)

        if amount not in [None, 0]:
            if amount > 0:
                self.stepper_running = True
                self.stepper.motor_run(
                    self.pins,
                    self.options_channels['step_delay'][0],
                    int(abs(amount)),
                    False,
                    False,
                    self.options_channels['step_resolution'][0],
                    .05)
                self.stepper_running = False
            elif amount < 0:
                self.stepper_running = True
                self.stepper.motor_run(
                    self.pins,
                    self.options_channels['step_delay'][0],
                    int(abs(amount)),
                    True,
                    False,
                    self.options_channels['step_resolution'][0],
                    .05)
                self.stepper_running = False
            measure_dict[0]['value'] = amount
            add_measurements_influxdb(self.unique_id, measure_dict)
        else:
            self.logger.error(
                "Invalid parameters: State: {state}, Type: {ot}, Amount: {amt}".format(
                    state=state,
                    ot=output_type,
                    amt=amount))

    def is_on(self, output_channel=None):
        if self.is_setup():
            return self.stepper_running

    def is_setup(self):
        return self.output_setup
